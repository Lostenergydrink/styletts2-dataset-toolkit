# StyleTTS2 Installation Guide

This guide walks you through setting up StyleTTS2 for fine-tuning on your custom dataset after preparing it with this toolkit.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone StyleTTS2](#clone-styletts2)
3. [Python Environment Setup](#python-environment-setup)
4. [Install Dependencies](#install-dependencies)
5. [Download Pretrained Models](#download-pretrained-models)
6. [Apply Code Patches](#apply-code-patches)
7. [Configure Training](#configure-training)
8. [Validate Setup](#validate-setup)
9. [Start Training](#start-training)

---

## Prerequisites

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3060 or better recommended)
- **RAM**: 16GB+ system RAM
- **Storage**: 10GB+ free space for models and checkpoints
- **CUDA**: 12.4 or compatible version

### Required Software

- **Python**: 3.10 or 3.11 (3.12+ not recommended)
- **Git**: For cloning repositories
- **espeak-ng**: Required by phonemizer
  - Download: https://github.com/espeak-ng/espeak-ng/releases
  - Install to default location: `C:\Program Files\eSpeak NG\`
  - Add to PATH if not automatic

---

## Clone StyleTTS2

```powershell
# Navigate to your projects directory
cd E:\AI\tts-webui

# Clone the official StyleTTS2 repository
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2
```

---

## Python Environment Setup

### Create Virtual Environment

**Option 1: Using venv (Recommended)**

```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option 2: Using conda**

```powershell
conda create -n styletts2 python=3.10
conda activate styletts2
```

### Verify Python Version

```powershell
python --version
# Should show: Python 3.10.x or 3.11.x
```

---

## Install Dependencies

### 1. Install PyTorch with CUDA Support

**Critical**: Install PyTorch 2.6.0+ for security fix (CVE-2025-32434)

```powershell
# For CUDA 12.4
pip install torch==2.6.0+cu124 torchaudio==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124

# Verify installation
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 2. Install Core Dependencies

Use the `requirements.txt` from this toolkit:

```powershell
# Copy requirements.txt from toolkit
copy E:\styletts2-dataset-toolkit\styletts2-setup\requirements.txt .\requirements_toolkit.txt

# Install dependencies (this may take 10-15 minutes)
pip install -r requirements_toolkit.txt
```

### 3. Install Additional StyleTTS2 Dependencies

```powershell
# Install phonemizer with espeak backend
pip install phonemizer

# Install monotonic_align (C++ extension)
cd monotonic_align
python setup.py build_ext --inplace
cd ..
```

### 4. Verify Key Packages

```powershell
python -c "import num2words; print('num2words OK')"
python -c "import tensorboard; print('tensorboard OK')"
python -c "import transformers; print('transformers OK')"
python -c "from phonemizer import phonemize; print('phonemizer OK')"
```

---

## Download Pretrained Models

StyleTTS2 requires several pretrained models for fine-tuning.

### 1. LibriTTS Pretrained Model

**Main checkpoint** (required for fine-tuning):

- **File**: `epochs_2nd_00020.pth`
- **Download**: [StyleTTS2 Models (Google Drive)](https://drive.google.com/drive/folders/1CJ8jbIT0qGfaIBTgb1U6RG4OI8VKXV05?usp=sharing)
- **Location**: Save to `Models/LibriTTS/`

```powershell
# Create directory
mkdir Models\LibriTTS

# After downloading, move file
move Downloads\epochs_2nd_00020.pth Models\LibriTTS\
```

### 2. ASR Model (Automatic Speech Recognition)

**Purpose**: Extracts phoneme alignments during training

- **File**: `epoch_00080.pth`
- **Download**: Same Google Drive link above
- **Location**: Save to `Utils/ASR/`

```powershell
mkdir Utils\ASR
move Downloads\epoch_00080.pth Utils\ASR\
```

### 3. F0 Model (Fundamental Frequency Estimator)

**Purpose**: Extracts pitch features

- **File**: `bst.t7` (JDC model)
- **Download**: Same Google Drive link above
- **Location**: Save to `Utils/JDC/`

```powershell
mkdir Utils\JDC
move Downloads\bst.t7 Utils\JDC\
```

### 4. PLBERT Model (Phoneme-Level BERT)

**Purpose**: Provides phoneme-level text representations

- **Repository**: https://huggingface.co/yl4579/StyleTTS2-LibriTTS
- **Files**: All files from the HuggingFace repo
- **Location**: Save to `Utils/PLBERT/`

```powershell
# Option 1: Download manually from HuggingFace
# https://huggingface.co/yl4579/StyleTTS2-LibriTTS/tree/main

# Option 2: Use git-lfs
git lfs install
git clone https://huggingface.co/yl4579/StyleTTS2-LibriTTS Utils\PLBERT
```

### Expected Directory Structure

```
StyleTTS2/
├── Models/
│   └── LibriTTS/
│       └── epochs_2nd_00020.pth
├── Utils/
│   ├── ASR/
│   │   └── epoch_00080.pth
│   ├── JDC/
│   │   └── bst.t7
│   └── PLBERT/
│       ├── config.json
│       ├── pytorch_model.bin
│       └── step_2000000.t7
└── Configs/
    └── config_ft.yml
```

---

## Apply Code Patches

This toolkit provides patches that fix critical bugs for Windows and add device compatibility.

### Run Patch Script

```powershell
# From the StyleTTS2 directory
cd E:\AI\tts-webui\StyleTTS2

# Run the patch application script from toolkit
E:\styletts2-dataset-toolkit\styletts2-setup\apply_patches.ps1
```

### What Gets Patched

- **train_finetune.py**: Device auto-detection (CPU/CUDA), optional tensorboard
- **meldataset.py**: Windows DataLoader fix (num_workers=0)
- **utils.py**: mask_from_lens fallback for incomplete PyPI package
- **models.py**: Multi-path resource loading
- **Modules/*.py**: Device-aware tensor creation

**Important**: Original files are backed up with `.original` extension.

### Manual Patch (if script fails)

```powershell
# Copy patches manually
copy E:\styletts2-dataset-toolkit\styletts2-setup\patches\train_finetune.py .\
copy E:\styletts2-dataset-toolkit\styletts2-setup\patches\meldataset.py .\
copy E:\styletts2-dataset-toolkit\styletts2-setup\patches\utils.py .\
copy E:\styletts2-dataset-toolkit\styletts2-setup\patches\models.py .\
copy E:\styletts2-dataset-toolkit\styletts2-setup\patches\Modules\*.py .\Modules\
```

---

## Configure Training

### 1. Copy Config Template

```powershell
# Copy the patched config from toolkit
copy E:\styletts2-dataset-toolkit\styletts2-setup\configs\config_ft.yml .\Configs\config_ft.yml
```

### 2. Edit Configuration

Open `Configs\config_ft.yml` and update paths:

```yaml
# Set device (auto, cuda, or cpu)
device: 'auto'

# Point to your prepared dataset
train_data: E:/your-dataset/train_list.txt
val_data: E:/your-dataset/val_list.txt

# Set batch sizes (adjust for your GPU VRAM)
batch_size: 16  # Reduce to 8 or 4 if out of memory

# Loader parameters (critical for Windows)
loader_params:
  train:
    batch_size: 16
    shuffle: true
    num_workers: 0  # Must be 0 on Windows
    drop_last: true
  val:
    batch_size: 8
    shuffle: false
    num_workers: 0  # Must be 0 on Windows
    drop_last: false

# Training parameters
epochs: 15
save_freq: 1  # Save checkpoint every epoch

# Pretrained model to fine-tune from
pretrained_model: Models/LibriTTS/epochs_2nd_00020.pth

# ASR, F0, and PLBERT models
ASR_config: Utils/ASR/config.yml
ASR_path: Utils/ASR/epoch_00080.pth
F0_path: Utils/JDC/bst.t7
PLBERT_dir: Utils/PLBERT/
```

### 3. Verify Dataset Paths

```powershell
# Check that manifest files exist
Test-Path E:\your-dataset\train_list.txt
Test-Path E:\your-dataset\val_list.txt

# Preview first few lines
Get-Content E:\your-dataset\train_list.txt -First 5
```

**Expected format**: `path/to/audio.wav|Transcription text here.|speaker_id`

---

## Validate Setup

### 1. Test Model Loading

```powershell
python -c "import torch; checkpoint = torch.load('Models/LibriTTS/epochs_2nd_00020.pth', map_location='cpu'); print('Checkpoint loaded OK')"
```

### 2. Test Dataset Loading

```powershell
# Quick validation script
python -c "
import yaml
with open('Configs/config_ft.yml', 'r') as f:
    config = yaml.safe_load(f)
print(f'Train data: {config[\"train_data\"]}')
print(f'Val data: {config[\"val_data\"]}')
print(f'Device: {config[\"device\"]}')
"
```

### 3. Validate Your Dataset

Before training, use the toolkit's validation script:

```powershell
python E:\styletts2-dataset-toolkit\styletts2-setup\validate_dataset.py E:\your-dataset\train_list.txt
python E:\styletts2-dataset-toolkit\styletts2-setup\validate_dataset.py E:\your-dataset\val_list.txt
```

**Fix any errors** before proceeding to training!

---

## Start Training

### Using the Launcher Script

```powershell
# Copy launcher from toolkit
copy E:\styletts2-dataset-toolkit\styletts2-setup\train_styletts2.ps1 .\

# Edit train_styletts2.ps1 to set correct paths
# Then run:
.\train_styletts2.ps1
```

### Manual Training

```powershell
# Activate venv if not already active
.\.venv\Scripts\Activate.ps1

# Start training
python train_finetune.py --config_path Configs/config_ft.yml
```

### Monitor Training

```powershell
# In a new terminal, start TensorBoard
tensorboard --logdir=Logs/
```

Open browser to http://localhost:6006

### Training Output

- **Checkpoints**: Saved to `Models/` directory
- **Logs**: Saved to `Logs/` directory
- **Expected time**: ~2-4 hours per epoch (varies by dataset size and GPU)

---

## Troubleshooting

### Common Issues

**1. Out of Memory Error**

```
RuntimeError: CUDA out of memory
```

**Solution**: Reduce `batch_size` in config (try 8, 4, or 2)

**2. Vocabulary Mismatch Error**

```
RuntimeError: size mismatch for text_encoder.embedding.weight
```

**Solution**: Your dataset has characters outside the 178-token vocabulary. Run normalization:

```powershell
python E:\styletts2-dataset-toolkit\styletts2-setup\normalize_dataset.py E:\your-dataset\train_list.txt
python E:\styletts2-dataset-toolkit\styletts2-setup\normalize_dataset.py E:\your-dataset\val_list.txt
```

**3. BERT Length Error**

```
Token indices sequence length is longer than 512
```

**Solution**: Your transcripts are too long (>450 characters). Edit or use toolkit's normalization with truncation.

**4. DataLoader Process Error (Windows)**

```
RuntimeError: DataLoader worker (pid XXXX) exited unexpectedly
```

**Solution**: Set `num_workers: 0` in config (should already be set if you used toolkit config)

**5. Missing num2words Module**

```
ModuleNotFoundError: No module named 'num2words'
```

**Solution**:

```powershell
pip install num2words
```

**6. Corrupted Virtual Environment**

If you encounter import errors or WinError 5 (Access Denied) on `.pyd` files:

```powershell
# Delete corrupted venv
deactivate
Remove-Item -Recurse -Force .venv

# Recreate fresh environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies in correct order
pip install torch==2.6.0+cu124 torchaudio==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements_toolkit.txt
```

### Still Having Issues?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more detailed error solutions.

---

## Next Steps

After successful training:

1. **Test your model**: Use StyleTTS2's inference scripts
2. **Monitor quality**: Listen to validation samples in TensorBoard
3. **Adjust hyperparameters**: Modify learning rate, batch size, epochs
4. **Continue training**: Resume from checkpoint if needed

---

## Additional Resources

- **StyleTTS2 Paper**: https://arxiv.org/abs/2306.07691
- **Official Repo**: https://github.com/yl4579/StyleTTS2
- **Dataset Requirements**: [DATASET_REQUIREMENTS.md](DATASET_REQUIREMENTS.md)
- **Preparation Guide**: [DATASET_PREP_GUIDE.md](DATASET_PREP_GUIDE.md)

---

*Last updated: November 2025*
