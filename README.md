# Quantization Extend & Deepfake Forensics

Este repositório contém ferramentas forenses avançadas para **atribuição de origem de imagens** (via Tabelas de Quantização JPEG/DQT) e **detecção de Deepfakes** (via análise de artefatos).

## 1. Forense de Imagem (DQT)
Ferramentas para extrair e comparar fingerprints de compressão JPEG. Útil para determinar se uma imagem foi salva no Photoshop, GIMP, Pixlr, etc.

### Scripts Principais (`scripts/`)
- `extrator_dqt_categorico.py`: Extrai DQTs de múltiplos datasets e gera banco de dados JSON.
- `comparador_forense.py`: Compara assinaturas entre softwares. Gera relatórios de colisão (Ex: `100%: gimp e pixlr são idênticos`).
- `gerar_dataset_sintetico.py`: Cria dataset controlado (Pixlr/PIL) de qualidade 1-100.

### Como Usar
```bash
# 1. Gerar Banco de Dados (lê de dataset/gimp, dataset/photoshop, etc)
python scripts/extrator_dqt_categorico.py

# 2. Gerar Relatório Comparativo
python scripts/comparador_forense.py
# Saída: output/relatorio_percentual.txt
```

---

## 2. Módulo de Detecção Deepfake (MVP)
Nova suíte de ferramentas isolada em `deepfake_module/` para análise científica de manipulação.

### Funcionalidades
1.  **Extração Forense de Frames** (`frame_extractor.py`)
    *   Extrai quadros de vídeo mantendo a **Cadeia de Custódia**.
    *   Calcula hash SHA-256 do vídeo original e de cada frame extraído.
2.  **Error Level Analysis (ELA)** (`analysis_ela.py`)
    *   Detecta anomalias de compressão (regiões coladas/modificadas).
3.  **Análise de Frequência (DFT)** (`analysis_frequency.py`)
    *   Gera espectrogramas para detectar padrões de grade (fingerprints de GANs).

### Como Usar o Módulo
```python
# Verificação rápida dos módulos
python scripts/verify_deepfake_module.py
```

### Exemplo de Integração (Python)
```python
from deepfake_module.frame_extractor import ForensicFrameExtractor
from deepfake_module.analysis_ela import ForensicELA

# 1. Extrair Frames com Hash
extractor = ForensicFrameExtractor()
report = extractor.extract_frames("evidencia.mp4", case_id="CASE_001")

# 2. Analisar Frame
ela = ForensicELA(quality=95)
ela.perform_ela("output/deepfake_analysis/CASE_001/frames/frame_00000.jpg", "ela_result.jpg")
```

---

## Estrutura do Projeto
```
.
├── dataset/                 # Datasets padrão (gimp, photoshop, pixlr)
├── deepfake_module/         # [NOVO] Módulo de detecção Deepfake isolado
├── output/                  # Resultados (JSONs, Relatórios, Heatmaps)
├── scripts/                 # Ferramentas de extração DQT
├── PLAN_DEEPFAKE_MVP.md     # Plano de implementação detalhado
└── README.md                # Esta documentação
```

## Créditos e Referências
- Datasets Originais: [jpeg-quantization-fingerprint](https://github.com/Cyber-Root0/jpeg-quantization-fingerprint.git)
- Metodologia: Análise de Quantização (DQT) e Artefatos de Compressão.
