import sys
import os
from pathlib import Path

# Add project root to path to allow imports from deepfake_module
sys.path.append(str(Path(__file__).parent.parent))

try:
    from deepfake_module.analysis_ela import ForensicELA
    from deepfake_module.analysis_frequency import ForensicFrequency
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def run_verification():
    print("=== INICIANDO VERIFICAÇÃO DO MÓDULO DEEPFAKE ===")
    
    # 1. Setup paths
    base_path = Path(r"c:\Users\klavy\dataset_rgb\quantization_extend") # Or current working dir
    # Fallback to local relative path if hardcoded doesn't exist (robustness)
    if not base_path.exists():
        base_path = Path(".")
        
    image_path = Path(r"c:\Users\klavy\Downloads\make this IA project\dataset\pixlr\100.jpg")
    output_dir = base_path / "output/verification"
    os.makedirs(output_dir, exist_ok=True)
    
    if not image_path.exists():
        print(f"ERRO: Imagem de teste não encontrada em {image_path}")
        # Try to find any jpg in dataset/pixlr
        alternatives = list(Path(r"c:\Users\klavy\Downloads\make this IA project\dataset\pixlr").glob("*.jpg"))
        if alternatives:
            image_path = alternatives[0]
            print(f"Usando alternativa: {image_path}")
        else:
            return

    print(f"Imagem de teste: {image_path}")
    
    # 2. Test ELA
    print("\n--- Testando ELA (Error Level Analysis) ---")
    try:
        ela = ForensicELA(quality=95)
        ela_out = output_dir / "test_ela.jpg"
        ela.perform_ela(str(image_path), str(ela_out))
        if ela_out.exists():
            print(f"✅ Sucesso! ELA salvo em {ela_out}")
        else:
            print("❌ Falha: Arquivo ELA não criado.")
    except Exception as e:
        print(f"❌ Erro no ELA: {e}")

    # 3. Test Frequency (DFT)
    print("\n--- Testando Análise de Frequência (DFT) ---")
    try:
        freq = ForensicFrequency()
        dft_out = output_dir / "test_dft.png"
        freq.perform_dft(str(image_path), str(dft_out))
        if dft_out.exists():
            print(f"✅ Sucesso! Espectro DFT salvo em {dft_out}")
        else:
            print("❌ Falha: Arquivo DFT não criado.")
    except Exception as e:
        print(f"❌ Erro no DFT: {e}")

    print("\n=== VERIFICAÇÃO CONCLUÍDA ===")

if __name__ == "__main__":
    run_verification()
