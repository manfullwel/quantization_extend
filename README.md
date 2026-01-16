# quantization_extend

Ferramentas para **extrair**, **versionar** e **comparar** tabelas de quantizacao JPEG (DQT) de forma escalavel e auditavel.

## Instalacao

```bash
pip install -e .
```

## Dataset esperado

Estrutura simples (igual seu projeto atual):

```
dataset/
  photoshop/
    90.jpg
    91.jpg
    ...
  gimp/
    90.jpg
    ...
```

O nome do arquivo pode ser `90.jpg` ou `quality_90.jpg` (o parser pega o primeiro numero do nome).

## Criar banco (JSON)

```bash
qext build-db --dataset ./dataset --out ./output/quant_db.json
```

## Match de um arquivo

```bash
qext match --db ./output/quant_db.json --input ./suspeita.jpg
```

## Saida (forense)

- hashes SHA-256 do arquivo
- tabelas Y/CbCr em 8x8
- fingerprint (qhash) de Y e C
- metadados JPEG (progressive, subsampling)

