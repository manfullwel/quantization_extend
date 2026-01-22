#!/usr/bin/env python3
"""
EXTRAÇÃO CATEGÓRICA DE DQTs - MVP Forense
Autor: [Seu Nome]
Data: 17/01/2026
Descrição: Extrai tabelas de quantização de arquivos JPEG de forma categórica
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import struct
import traceback

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    print("AVISO: PIL (Pillow) não instalado. Metadados técnicos serão limitados.")
    HAS_PIL = False

from dataclasses import dataclass, asdict

class ExtratorDQTCategorico:
    """Extrator categórico de DQTs - FOCADO NO SEU OBJETIVO"""
    
    def __init__(self):
        self.resultados = []
    
    def extrair_dqt_direto_header(self, caminho_arquivo: str) -> Optional[Dict]:
        """
        Extrai DQTs LENDO DIRETAMENTE o header JPEG
        Método mais preciso e forense
        """
        try:
            with open(caminho_arquivo, 'rb') as f:
                dados = f.read()
            
            # Procurar segmentos DQT (0xFFDB)
            dqt_tables = []
            i = 0
            
            while i < len(dados) - 1:
                # Encontrar marcador 0xFF
                if dados[i] == 0xFF:
                    marker = dados[i+1]
                    
                    # Marcador DQT (Define Quantization Table)
                    if marker == 0xDB:
                        # Tamanho do segmento (2 bytes, big-endian)
                        length = struct.unpack('>H', dados[i+2:i+4])[0]
                        
                        # Dados da tabela (começa em i+4)
                        # Length inclui os 2 bytes de tamanho.
                        # Exemplo: Length=67 -> 2 bytes (len) + 65 bytes (dados)
                        # Dados vão de i+4 até i+2+length
                        dqt_data = dados[i+4 : i+2+length]
                        
                        # Processar o segmento DQT
                        # Um segmento DQT pode conter múltiplas tabelas
                        pos = 0
                        while pos < len(dqt_data):
                            # Se sobrar menos bytes que o cabeçalho de uma tabela (1 byte), para
                            if pos >= len(dqt_data):
                                break
                                
                            # Extrair informações da tabela
                            # Primeiro byte: precisão (0=8 bits) e identificador (0-3)
                            info = dqt_data[pos]
                            precision = (info >> 4) & 0x0F  # 0 ou 1
                            table_id = info & 0x0F  # 0-3
                            pos += 1
                            
                            # Validar se tem dados suficientes
                            bytes_needed = 64 * (1 if precision == 0 else 2)
                            if pos + bytes_needed > len(dqt_data):
                                print(f"AVISO: Segmento DQT truncado ou malformado em {caminho_arquivo}")
                                break
                            
                            # Os próximos 64 bytes são os valores da tabela
                            table_values = []
                            for j in range(64):
                                if precision == 0:  # 8-bit precision
                                    val = dqt_data[pos + j]
                                    step = 1
                                else:  # 16-bit precision (raro)
                                    val = struct.unpack('>H', dqt_data[pos + 2*j:pos + 2*(j+1)])[0]
                                    step = 2
                                table_values.append(val)
                            
                            pos += bytes_needed
                            
                            # Converter para matriz 8x8 (zigzag order)
                            zigzag = [
                                0,  1,  5,  6, 14, 15, 27, 28,
                                2,  4,  7, 13, 16, 26, 29, 42,
                                3,  8, 12, 17, 25, 30, 41, 43,
                                9, 11, 18, 24, 31, 40, 44, 53,
                                10, 19, 23, 32, 39, 45, 52, 54,
                                20, 22, 33, 38, 46, 51, 55, 60,
                                21, 34, 37, 47, 50, 56, 59, 61,
                                35, 36, 48, 49, 57, 58, 62, 63
                            ]
                            
                            matriz_8x8 = []
                            for row in range(8):
                                linha = []
                                for col in range(8):
                                    idx = zigzag[row * 8 + col]
                                    linha.append(table_values[idx])
                                matriz_8x8.append(linha)
                            
                            dqt_tables.append({
                                'id': table_id,
                                'precision': precision,
                                'valores': matriz_8x8,
                                'tipo': 'Y' if table_id in [0, 1] else 'C'
                            })
                        
                        # Avançar para o próximo marcador
                        # Marker(2) + Length(L). O offset avança 2 + Length?
                        # i estava em FF.
                        # Próximo deve ser i + 2 + Length.
                        i += 2 + length
                        continue
                        
                    elif marker == 0xDA: # SOS - Start of Scan
                        # Geralmente header acaba aqui. Para performance, podemos parar.
                        pass
                
                i += 1
            
            # Organizar as tabelas (normalmente: Y primeiro, C depois)
            if len(dqt_tables) >= 2:
                # Simple heuristic: table 0 is Y, table 1 is C (if distinct IDs found)
                # Better: search for ID 0 then ID 1
                dqt_y = None
                dqt_c = None
                
                # Find Y (ID 0)
                for t in dqt_tables:
                    if t['id'] == 0:
                        dqt_y = t['valores']
                        break
                if dqt_y is None and len(dqt_tables) > 0:
                     dqt_y = dqt_tables[0]['valores']
                     
                # Find C (ID 1)
                for t in dqt_tables:
                    if t['id'] == 1:
                        dqt_c = t['valores']
                        break
                if dqt_c is None and len(dqt_tables) > 1:
                    dqt_c = dqt_tables[1]['valores']
                    
                return {
                    'Y': dqt_y,
                    'C': dqt_c
                }
            elif len(dqt_tables) == 1:
                return {'Y': dqt_tables[0]['valores'], 'C': None}
            
        except Exception as e:
            print(f"Erro na extração direta em {caminho_arquivo}: {e}")
            traceback.print_exc()
        
        return None
    
    def calcular_hash_tabela(self, tabela: List[List[int]]) -> str:
        """Calcula hash SHA-256 da tabela DQT"""
        if not tabela:
            return ""
        
        # Converter matriz para string única
        tabela_str = ""
        for linha in tabela:
            tabela_str += ",".join(str(v) for v in linha) + "|"
        
        return hashlib.sha256(tabela_str.encode()).hexdigest()
    
    def extrair_parametros_nome(self, nome_arquivo: str) -> Dict:
        """
        Extrai parâmetros do nome do arquivo.
        Suporta:
        1. pixlr_100_444.jpg -> software=pixlr, q=100
        2. 100.jpg -> software=?, q=100 (software deve vir do contexto)
        """
        nome_sem_ext = Path(nome_arquivo).stem
        partes = nome_sem_ext.split('_')
        
        # Tenta detectar se é apenas um número (Quality.jpg)
        if len(partes) == 1 and partes[0].isdigit():
            return {
                'software': None, # Será preenchido pelo info_adicional
                'qualidade': int(partes[0]),
                'subsampling': 'unknown',
                'progressive': False
            }

        # Formato complexo: software_qualidade_...
        software = partes[0] if len(partes) > 0 else 'desconhecido'
        qualidade = 0
        if len(partes) > 1:
            try:
                qualidade = int(partes[1])
            except ValueError:
                pass
        
        subsampling = 'unknown'
        if len(partes) > 2:
            subsampling = partes[2]
            
        progressive = False
        if len(partes) > 3 and 'prog' in partes[3].lower():
            progressive = True
            
        params = {
            'software': software,
            'qualidade': qualidade,
            'subsampling': subsampling,
            'progressive': progressive
        }
        
        return params
    
    def processar_arquivo(self, caminho_completo: str, info_adicional: Dict = None) -> Dict:
        """
        Processa UM arquivo JPEG e extrai TUDO categoricamente
        """
        arquivo = Path(caminho_completo)
        
        # 1. Extrair parâmetros do nome
        params_nome = self.extrair_parametros_nome(arquivo.name)
        
        # Merge com info_adicional se necessário
        software_final = params_nome['software']
        if (software_final is None or software_final.isdigit()) and info_adicional:
            software_final = info_adicional.get('software', 'desconhecido')
            
        qualidade_final = params_nome['qualidade']
        
        # 2. Hash do arquivo

        try:
            with open(arquivo, 'rb') as f:
                hash_arquivo = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Erro ao ler arquivo {arquivo}: {e}")
            return None
        
        # 3. Extrair DQTs DIRETO do header
        dqts = self.extrair_dqt_direto_header(caminho_completo)
        
        if not dqts:
            print(f"AVISO: Não encontrou DQTs em {arquivo.name}")
            return None
        
        # 4. Calcular hashes das tabelas
        hash_y = self.calcular_hash_tabela(dqts.get('Y'))
        hash_c = self.calcular_hash_tabela(dqts.get('C'))
        
        # 5. Montar resultado CATEGÓRICO
        resultado = {
            # INFORMAÇÕES CATEGÓRICAS
            "informacoes_categoricas": {
                "software": software_final,
                "versao_software": info_adicional.get('versao', 'desconhecida') if info_adicional else 'desconhecida',
                "modo_exportacao": info_adicional.get('modo', 'Export') if info_adicional else 'Export',
                "fator_qualidade": qualidade_final,
                "subsampling": params_nome['subsampling'],
                "progressive": params_nome['progressive'],
                "categoria_forense": f"{software_final}_Q{qualidade_final}"
            },
            
            # TABELAS DE QUANTIZAÇÃO
            "tabelas_quantizacao": {
                "luminancia_Y": dqts.get('Y'),
                "crominancia_C": dqts.get('C'),
                "hashes": {
                    "hash_y": hash_y,
                    "hash_c": hash_c
                }
            },
            
            # INFORMAÇÕES DO ARQUIVO
            "arquivo": {
                "nome": arquivo.name,
                "caminho": str(arquivo),
                "tamanho_bytes": arquivo.stat().st_size,
                "sha256": hash_arquivo
            },
            
            # METADADOS TÉCNICOS
            "metadados_tecnicos": self.extrair_metadados_simples(caminho_completo)
        }
        
        self.resultados.append(resultado)
        return resultado
    
    def extrair_metadados_simples(self, caminho_arquivo: str) -> Dict:
        """Extrai metadados técnicos básicos"""
        if not HAS_PIL:
            # Tentar recuperar dimensoes via SOF se PIL falhar? Opcional.
            return {"erro": "PIL não instalado"}
            
        try:
            with Image.open(caminho_arquivo) as img:
                return {
                    "dimensoes": f"{img.width}x{img.height}",
                    "formato": img.format,
                    "modo": img.mode,
                    "bits_per_sample": img.bits if hasattr(img, 'bits') else 8
                }
        except:
            return {"erro": "Não foi possível extrair metadados"}
    
    def processar_diretorio_completo(self, diretorio: str, software_info: Dict) -> List[Dict]:
        """
        Processa TODOS os arquivos de um diretório
        """
        diretorio_path = Path(diretorio)
        
        if not diretorio_path.exists():
            print(f"ERRO: Diretório não existe: {diretorio}")
            return []
        
        # Listar todos os JPEGs
        arquivos_jpeg = list(diretorio_path.glob("*.jpg")) + list(diretorio_path.glob("*.jpeg"))
        
        print(f"Encontrados {len(arquivos_jpeg)} arquivos JPEG em {diretorio}")
        
        resultados = []
        for arquivo in sorted(arquivos_jpeg, key=lambda x: x.name):
            print(f"Processando: {arquivo.name}")
            
            resultado = self.processar_arquivo(str(arquivo), software_info)
            if resultado:
                resultados.append(resultado)
        
        return resultados
    
    def salvar_resultados_json(self, caminho_saida: str = "resultados_dqt_categoricos.json"):
        """Salva todos os resultados em JSON formatado"""
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Resultados salvos em: {caminho_saida}")
        print(f"📊 Total de arquivos processados: {len(self.resultados)}")
    
    def gerar_relatorio_resumo(self) -> Dict:
        """Gera um resumo estatístico dos resultados"""
        if not self.resultados:
            return {}
        
        # Agrupar por software e qualidade
        resumo = {}
        
        for resultado in self.resultados:
            software = resultado['informacoes_categoricas']['software']
            qualidade = resultado['informacoes_categoricas']['fator_qualidade']
            
            if software not in resumo:
                resumo[software] = {
                    'total_arquivos': 0,
                    'qualidades_processadas': [],
                    'tabelas_unicas_y': set(),
                    'tabelas_unicas_c': set()
                }
            
            resumo[software]['total_arquivos'] += 1
            resumo[software]['qualidades_processadas'].append(qualidade)
            
            try:
                hash_y = resultado['tabelas_quantizacao']['hashes']['hash_y']
                hash_c = resultado['tabelas_quantizacao']['hashes']['hash_c']
                
                resumo[software]['tabelas_unicas_y'].add(hash_y)
                if hash_c:
                    resumo[software]['tabelas_unicas_c'].add(hash_c)
            except Exception as e:
                print(f"Erro ao gerar resumo para {resultado['arquivo']['nome']}: {e}")
        
        # Converter sets para listas para JSON
        for software in resumo:
            resumo[software]['tabelas_unicas_y'] = list(resumo[software]['tabelas_unicas_y'])
            resumo[software]['tabelas_unicas_c'] = list(resumo[software]['tabelas_unicas_c'])
            resumo[software]['qualidades_processadas'] = sorted(list(set(resumo[software]['qualidades_processadas'])))
        
        return resumo

# USO PRÁTICO
def main():
    """Exemplo de uso categórico para múltiplos datasets"""
    
    # 1. Inicializar extrator
    extrator = ExtratorDQTCategorico()
    
    base_path = Path(r"c:\Users\klavy\Downloads\make this IA project")
    
    # 2. Configurar diretórios e metadados
    datasets = [
        {
            "dir": base_path / "dataset/pixlr",
            "info": {
                "software": "pixlr",
                "versao": "Online 2026",
                "modo": "Export",
                "observacao": "Dataset Sintético Gerado (PIL)"
            }
        },
        {
            "dir": base_path / "dataset/jpeg-quantization-fingerprint/dataset/gimp",
            "info": {
                "software": "gimp",
                "versao": "Unknown",
                "modo": "Save/Export",
                "observacao": "Dataset externo clonado"
            }
        },
        {
            "dir": base_path / "dataset/jpeg-quantization-fingerprint/dataset/photoshop",
            "info": {
                "software": "photoshop",
                "versao": "Unknown",
                "modo": "Save As",
                "observacao": "Dataset externo clonado"
            }
        }
    ]
    
    print("=" * 60)
    print("INICIANDO PROCESSO FORENSE - MÚLTIPLOS DATASETS")
    print("=" * 60)
    
    total_processed = 0
    
    for ds in datasets:
        dpath = ds['dir']
        dinfo = ds['info']
        
        if dpath.exists():
            print(f"\n📂 Processando Dataset: {dinfo['software'].upper()}")
            print(f"   Caminho: {dpath}")
            
            resultados = extrator.processar_diretorio_completo(
                diretorio=str(dpath),
                software_info=dinfo
            )
            count = len(resultados)
            print(f"   ✅ Extraídos: {count} arquivos")
            total_processed += count
        else:
            print(f"\n⚠️ Dataset não encontrado: {dpath}")

    # 3. Salvar resultados UNIFICADOS em JSON
    output_json = base_path / "output/forensic_db_combined.json"
    
    # Criar diretório de output se não existir
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    extrator.salvar_resultados_json(str(output_json))
    
    # 4. Gerar resumo estatístico
    resumo = extrator.gerar_relatorio_resumo()
    
    print("\n" + "=" * 60)
    print("RESUMO ESTATÍSTICO GLOBAL")
    print("=" * 60)
    
    for software, dados in resumo.items():
        print(f"\n📁 {software}:")
        print(f"   Arquivos processados: {dados['total_arquivos']}")
        print(f"   Qualidades encontradas: {len(dados['qualidades_processadas'])}")
        # Mostrar range de qualidade resumido
        quals = dados['qualidades_processadas']
        if len(quals) > 10:
             print(f"   Range Qualidade: {min(quals)} - {max(quals)}")
        else:
             print(f"   Qualidades: {quals}")
        
        print(f"   Tabelas DQT-Y únicas: {len(dados['tabelas_unicas_y'])}")
        print(f"   Tabelas DQT-C únicas: {len(dados['tabelas_unicas_c'])}")


if __name__ == "__main__":
    main()
