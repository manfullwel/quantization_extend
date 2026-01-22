import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

class ForensicFrequency:
    """
    Frequency Domain Analysis for detecting GAN artifacts.
    Generates Spectrograms using 2D DFT.
    """
    
    def perform_dft(self, image_path: str, output_path: Optional[str] = None):
        """
        Computes 2D Discrete Fourier Transform and Azimuthal Average.
        Saves a plot of the Magnitude Spectrum.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # 1. Load as Grayscale
        img = cv2.imread(str(image_path), 0)
        if img is None:
            raise ValueError("Could not read image.")
            
        # 2. DFT
        dft = cv2.dft(np.float32(img), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 3. Magnitude Spectrum (Log scale for visibility)
        magnitude_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]) + 1)
        
        # 4. Azimuthal Average (1D profile)
        # Calculate radial average... (Simplified version for MVP: just spectrum plot)
        
        # 5. Generate Forensic Plot
        plt.figure(figsize=(10, 5))
        
        plt.subplot(121)
        plt.imshow(img, cmap='gray')
        plt.title('Input Image')
        plt.axis('off')
        
        plt.subplot(122)
        plt.imshow(magnitude_spectrum, cmap='gray')
        plt.title('Magnitude Spectrum (DFT)')
        plt.axis('off')
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            plt.close()
            print(f"Spectrum saved to {output_path}")
        else:
            plt.show()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        freq = ForensicFrequency()
        try:
            out = f"dft_{Path(sys.argv[1]).stem}.png"
            freq.perform_dft(sys.argv[1], out)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Create dummy file for testing without args
        print("Usage: python analysis_frequency.py <image_path>")
