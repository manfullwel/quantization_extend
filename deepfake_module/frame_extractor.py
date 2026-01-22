import cv2
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

class ForensicFrameExtractor:
    """
    Extracts frames from video evidence for forensic analysis.
    Ensures Chain of Custody by hashing input video and extracted frames.
    """
    
    def __init__(self, output_base: str = "output/deepfake_analysis"):
        self.output_base = Path(output_base)
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculates SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_frames(self, video_path: str, case_id: str, max_frames: int = 50) -> Dict:
        """
        Extracts I-frames (or regular interval frames) from video.
        Returns a report with hashes.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
            
        # 1. Setup Case Directory
        case_dir = self.output_base / case_id / "frames"
        os.makedirs(case_dir, exist_ok=True)
        
        # 2. Hash Input Video (Chain of Custody)
        print(f"Hashing input video: {video_path.name}...")
        input_hash = self.calculate_file_hash(video_path)
        
        # 3. Open Video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        extracted_frames = []
        frame_count = 0
        saved_count = 0 
        
        # Strategy: Extract frames at regular intervals to span the video
        # or max_frames if video is short.
        step = max(1, total_frames // max_frames)
        
        print(f"Extracting frames from {video_path.name} (Total: {total_frames}, Step: {step})")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % step == 0 and saved_count < max_frames:
                frame_filename = f"frame_{frame_count:05d}.jpg"
                output_path = case_dir / frame_filename
                
                # Save Frame (High Quality JPEG)
                cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
                
                # Hash Extracted Frame
                frame_hash = self.calculate_file_hash(output_path)
                
                extracted_frames.append({
                    "frame_index": frame_count,
                    "filename": frame_filename,
                    "path": str(output_path),
                    "sha256": frame_hash
                })
                saved_count += 1
                
            frame_count += 1
            
        cap.release()
        
        report = {
            "case_id": case_id,
            "source_video": {
                "filename": video_path.name,
                "path": str(video_path),
                "sha256": input_hash,
                "total_frames": total_frames,
                "fps": fps
            },
            "extraction": {
                "method": "uniform_interval",
                "extracted_count": len(extracted_frames),
                "frames": extracted_frames
            }
        }
        
        # Save Extraction Report
        report_path = self.output_base / case_id / "extraction_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        return report

if __name__ == "__main__":
    # Test if run directly
    import sys
    if len(sys.argv) > 2:
        extractor = ForensicFrameExtractor()
        try:
            rep = extractor.extract_frames(sys.argv[1], sys.argv[2])
            print(f"Success! extracted {rep['extraction']['extracted_count']} frames.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python frame_extractor.py <video_path> <case_id>")
