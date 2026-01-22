#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from collections import defaultdict

def main():
    json_path = Path(r"c:\Users\klavy\Downloads\make this IA project\output\forensic_db_combined.json")
    
    if not json_path.exists():
        print("JSON não encontrado.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Organizar dados por Qualidade -> Software -> Hash
    # Estrutura: db[qualidade][software] = hash_y
    db = defaultdict(dict)
    
    softwares_presentes = set()

    for entry in data:
        info = entry['informacoes_categoricas']
        hashes = entry['tabelas_quantizacao']['hashes']
        
        software = info['software']
        qualidade = info['fator_qualidade']
        hash_y = hashes['hash_y']
        
        db[qualidade][software] = hash_y
        softwares_presentes.add(software)
        
    sorted_softwares = sorted(list(softwares_presentes))
    print("="*60)
    print("MATCHES POR PORCENTAGEM DE QUALIDADE (GIMP vs PHOTOSHOP vs PIXLR)")
    print("="*60)
    
    # Iterar de 1 a 100
    for q in range(1, 101):
        if q not in db:
            continue
            
        hashes_at_q = db[q]
        
        # Agrupar softwares por hash
        reverse_map = defaultdict(list)
        
        # Garantir que verificamos todos os softwares esperados, mesmo se hash for nulo (improvável aqui, mas bom pra robustez)
        for sw in sorted_softwares:
            if sw in hashes_at_q:
                h = hashes_at_q[sw]
                reverse_map[h].append(sw)
            else:
                reverse_map["missing"].append(sw)
        
        # Formatar a saída
        # Ex: gimp vs photoshop e pixlr são idênticos
        
        grupos_strings = []
        
        # Ordenar os grupos para consistência visual
        # Primeiro grupos maiores (matches), depois alfabético
        sorted_groups = sorted(reverse_map.values(), key=lambda x: (-len(x), x[0]))
        
        for group in sorted_groups:
            if len(group) > 1:
                # Se houver match, usar separador 'e' e adicionar sufixo
                s = " e ".join(sorted(group))
                grupos_strings.append(f"{s} são idênticos")
            else:
                # Se for único, apenas o nome
                grupos_strings.append(group[0])
                
        # Juntar tudo com ' vs '
        linha_comparacao = " vs ".join(grupos_strings)
        
        print(f"{q}%: {linha_comparacao}")

if __name__ == "__main__":
    # Forçar saída UTF-8 para evitar erros de encoding no console/arquivo Windows
    sys.stdout.reconfigure(encoding='utf-8')
    main()
