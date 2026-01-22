import cv2
import numpy as np
from pathlib import Path
import os
from typing import Optional, Tuple

class ForensicELA:
    """
    Error Level Analysis (ELA) for detecting digital manipulation.
    Highlights regions with different JPEG compression levels.
    """
    
    def __init__(self, quality: int = 95):
        self.quality = quality
        
    def perform_ela(self, image_path: str, output_path: Optional[str] = None) -> Tuple[np.ndarray, float]:
        """
        Performs ELA on the input image.
        Returns: (ela_image, max_diff_value)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # 1. Load Original
        original = cv2.imread(str(image_path))
        if original is None:
            raise ValueError("Could not read image structure.")
            
        # 2. Resave at known quality (Virtual/Memory buffer preferred to avoid disk I/O, but disk is standard for ELA)
        # Using memory buffer for speed and clean forensic separation
        _, encoded_img = cv2.imencode('.jpg', original, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        resaved = cv2.imdecode(encoded_img, 1)
        
        # 3. Calculate Absolute Difference
        # 1.0 * orig - resaved to allow float arithmetic
        diff = cv2.absdiff(original, resaved)
        
        # 4. Enhance the difference (Forensic Scaling)
        # Find local max to scale
        max_diff = np.max(diff)
        if max_diff == 0:
            scale = 1
        else:
            # Scale to use full 0-255 range for visibility
            scale = 255.0 / max_diff
            
        ela_image = cv2.convertScaleAbs(diff, alpha=scale)
        
        # 5. Save if output path provided
        if output_path:
            cv2.imwrite(output_path, ela_image)
            
        return ela_image, max_diff

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ela = ForensicELA()
        try:
            out = f"ela_{Path(sys.argv[1]).name}"
            ela.perform_ela(sys.argv[1], out)
            print(f"ELA saved to {out}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python analysis_ela.py <image_path>")
