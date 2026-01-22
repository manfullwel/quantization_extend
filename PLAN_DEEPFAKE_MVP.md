# Forensic Deepfake Detection MVP Plan

## Goal Description
Implement a robust, evidence-based Deepfake Detection module as an independent extension to the `quantization_extend` repository. This module will focus on "scientific reliability" avoiding guesswork, by implementing proven forensic techniques (ELA, Frequency Analysis, Face Artifacts) **without modifying the core DQT extraction code**.

## User Review Required
> [!IMPORTANT]
> The module will be strictly isolated in `deepfake_module/`. No changes will be made to `extract.py` or existing scripts to ensure zero regression on the DQT project.

## Proposed Architecture
Directory Structure Additions:
```
quantization_extend/
├── deepfake_module/         <-- NEW ISOLATED MODULE
│   ├── __init__.py
│   ├── frame_extractor.py   (Extract I-frames from video with hash verification)
│   ├── face_detector.py     (ROI isolation using MTCNN/dlib)
│   ├── analysis_ela.py      (Error Level Analysis for compression inconsistencies)
│   ├── analysis_frequency.py (DFT/DCT for GAN spectral artifacts)
│   └── report_generator.py  (Forensic JSON log)
```

## Implementation Steps

### 1. Frame Extraction & Integrity (`frame_extractor.py`)
- **Objective**: Extract investigable frames from video evidence maintaining chain of custody.
- **Forensic**: Log SHA-256 of the input video and every extracted frame found.
- **Tech**: `opencv-python`.

### 2. Face Detection ROI (`face_detector.py`)
- **Objective**: Isolate facial regions for targeted analysis.
- **Forensic**: Crop faces with fixed margins to analyze boundary artifacts.
- **Tech**: `mtcnn` or `dlib` (will check availability).

### 3. Forensic Analysis Methods
#### [NEW] `analysis_ela.py` (Error Level Analysis)
- **Concept**: Digital modifications often have different JPEG compression levels than the background.
- **Method**: Resave image at 95% quality and difference map.
- **Output**: Heatmap showing high-variance regions (suspicious).

#### [NEW] `analysis_frequency.py` (Spectral Analysis)
- **Concept**: GANs leave traces in high-frequency domains (grid patterns) invisible to the naked eye.
- **Method**: 2D-DFT (Discrete Fourier Transform) + Azimuthal Average.
- **Output**: 1D power spectrum plot/data.

## Verification Plan
### Automated Tests
- **Integrity**: Verify extracted frames match expected hashes.
- **Detection**: Run ELA on a "tampered" synthetic image (e.g., from our Pixlr dataset) and verify heatmap generation.
