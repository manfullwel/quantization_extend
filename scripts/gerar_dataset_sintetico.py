#!/usr/bin/env python3
import os
from pathlib import Path
from PIL import Image

def main():
    # Configuração
    source_image_path = Path(r"c:\Users\klavy\Downloads\make this IA project\img_pixlr\pixlr_100.jpg")
    output_dir = Path(r"c:\Users\klavy\Downloads\make this IA project\dataset\pixlr")
    
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    if not source_image_path.exists():
        print(f"Erro: Imagem fonte não encontrada em {source_image_path}")
        return

    print(f"Gerando dataset em: {output_dir}")
    print(f"Fonte: {source_image_path}")

    try:
        with Image.open(source_image_path) as img:
            # Converter para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Gerar qualidades de 1 a 100
            for q in range(1, 101):
                filename = f"{q}.jpg"
                output_path = output_dir / filename
                
                # Salvar com a qualidade específica
                # subsampling=0 garante 4:4:4 para qualidades altas se o encoder suportar,
                # mas padrão do PIL é variar. Vamos deixar padrão para simular variação real.
                img.save(output_path, "JPEG", quality=q)
                
                print(f"Gerado: {filename} (Qualidade {q})")
                
    except Exception as e:
        print(f"Erro ao processar: {e}")

    print("="*40)
    print(f"Dataset gerado com sucesso! Total: 100 imagens.")

if __name__ == "__main__":
    main()
