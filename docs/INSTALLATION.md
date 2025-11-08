# 📥 Installation Guide

Complete installation instructions for the StyleTTS2 Dataset Toolkit on Windows.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **GPU**: NVIDIA GPU with CUDA support
  - Minimum: RTX 2060 (6GB VRAM)
  - Recommended: RTX 3060 or higher (12GB+ VRAM)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 50GB+ free space recommended
  - Models: ~5-10GB
  - Datasets: varies by size
  - Dependencies: ~5GB per environment

### Software Requirements
1. **Python 3.10 or 3.11**
   - Download: https://www.python.org/downloads/
   - ⚠️ Make sure to check "Add Python to PATH" during installation
   - ⚠️ Python 3.12 may have compatibility issues

2. **CUDA Toolkit 12.1+** (for GPU acceleration)
   - Download: https://developer.nvidia.com/cuda-downloads
   - Installation guide: https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/

3. **FFmpeg** (for audio processing)
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract to `E:\AI\tools\ffmpeg\` or update paths in launchers
   - Add to PATH: `E:\AI\tools\ffmpeg\bin`

4. **Git** (optional, for cloning)
   - Download: https://git-scm.com/download/win

---

## 🚀 Installation Steps

### Step 1: Clone/Download Repository

**Option A: With Git**
```powershell
cd E:\  # Or your preferred location
git clone https://github.com/Lostenergydrink/styletts2-dataset-toolkit.git
cd styletts2-dataset-toolkit
```

**Option B: Manual Download**
1. Download ZIP from GitHub
2. Extract to `E:\styletts2-dataset-toolkit\`
3. Open PowerShell in that directory

### Step 2: Install Stem Separation

```powershell
cd stem-separation

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install PyTorch with CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
pip install -r requirements.txt

# Test installation
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

**Expected output:**
```
CUDA Available: True
```

If `False`, check your NVIDIA drivers and CUDA installation.

### Step 3: Install StyleTTS2

```powershell
cd ..\styletts2-setup

# Create isolated virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install PyTorch with CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install StyleTTS2 and dependencies
pip install styletts2
pip install gradio>=4.0.0
pip install openai-whisper
pip install pydub librosa soundfile

# Test installation
python -c "import styletts2; print('StyleTTS2 installed successfully!')"
```

### Step 4: Configure FFmpeg

**If FFmpeg is in a custom location:**

1. Edit `stem-separation\launch_stem_separation.bat`:
   ```bat
   REM Update this line:
   set PATH=E:\AI\tools\ffmpeg\bin;%PATH%
   ```

2. Edit `styletts2-setup\launch_styletts2.ps1`:
   ```powershell
   # Update this line:
   $env:PATH = "E:\AI\tools\ffmpeg\bin;$env:PATH"
   ```

**Verify FFmpeg:**
```powershell
ffmpeg -version
```

Should show FFmpeg version info.

---

## ✅ Verify Installation

### Test Stem Separation

```powershell
cd stem-separation
.\launch_stem_separation.bat
```

Should open browser to `http://127.0.0.1:7861`

**Check:**
- ✅ "Device: cuda"
- ✅ "GPU: [Your GPU Name]"
- ✅ "Demucs Available: True"
- ✅ "UVR Models Available: True"

### Test StyleTTS2

```powershell
cd ..\styletts2-setup
.\launch_styletts2.bat
```

Should open browser to `http://localhost:7860`

**Check:**
- ✅ "CUDA Available: True"
- ✅ GPU detected
- ✅ Model loads without errors

---

## 🔧 Troubleshooting

### "Python not recognized"
- Python not in PATH
- **Fix**: Reinstall Python, check "Add to PATH"
- Or add manually: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\`

### "CUDA out of memory"
- GPU VRAM full
- **Fix**: Close other GPU applications
- **Fix**: Use lower quality preset (Balanced instead of Maximum)
- **Fix**: Process shorter audio files

### "FFmpeg not found"
- FFmpeg not in PATH
- **Fix**: Update batch/PowerShell scripts with correct FFmpeg path
- **Fix**: Add FFmpeg to system PATH permanently

### "torch.cuda.is_available() returns False"
- CUDA not detected
- **Fix**: Install/update NVIDIA drivers
- **Fix**: Install CUDA Toolkit 12.1+
- **Fix**: Reinstall PyTorch with correct CUDA version:
  ```powershell
  pip uninstall torch torchaudio
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### "ModuleNotFoundError: No module named 'demucs'"
- Wrong virtual environment activated
- **Fix**: Ensure you activated the correct venv:
  - Stem separation: `stem-separation\venv\Scripts\Activate.ps1`
  - StyleTTS2: `styletts2-setup\.venv\Scripts\Activate.ps1`

### "Cannot run scripts (Execution Policy)"
- PowerShell execution policy restricted
- **Fix**: Run PowerShell as Administrator:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Models downloading slowly
- Hugging Face models downloading from China/outside US
- **Fix**: Use VPN or mirror
- **Fix**: Pre-download models manually to cache directories

---

## 🔄 Updating

### Update Stem Separation
```powershell
cd stem-separation
.\venv\Scripts\Activate.ps1
pip install --upgrade demucs audio-separator gradio
```

### Update StyleTTS2
```powershell
cd styletts2-setup
.\.venv\Scripts\Activate.ps1
pip install --upgrade styletts2 gradio
```

---

## 📁 Directory Structure After Installation

```
E:\styletts2-dataset-toolkit\
├── stem-separation\
│   ├── venv\                      # Virtual environment
│   ├── stem_separation_webui.py
│   ├── batch_separate.py
│   ├── launch_stem_separation.bat
│   ├── requirements.txt
│   ├── models\                    # Downloaded Demucs models
│   └── stem-outputs\              # Output directory
│
├── styletts2-setup\
│   ├── .venv\                     # Virtual environment
│   ├── launch_styletts2.bat
│   ├── launch_styletts2.ps1
│   ├── models\                    # StyleTTS2 models
│   ├── outputs\                   # Generated audio
│   ├── datasets\                  # Training datasets
│   ├── training-data\             # Raw/processed audio
│   └── voice-samples\             # Reference audio
│
├── docs\
└── examples\
```

---

## 🎯 Post-Installation Checklist

- [ ] Python 3.10/3.11 installed and in PATH
- [ ] CUDA Toolkit 12.1+ installed
- [ ] NVIDIA drivers up to date
- [ ] FFmpeg installed and accessible
- [ ] Stem separation venv created and working
- [ ] StyleTTS2 venv created and working
- [ ] CUDA available in both environments
- [ ] Both web UIs launch successfully
- [ ] GPU detected and used by default

---

## 💡 Tips

### Storage Optimization
- Store models on E: drive (if you have multiple drives)
- Set cache directories:
  ```powershell
  $env:HF_HOME = "E:\AI\.cache\huggingface"
  $env:TORCH_HOME = "E:\AI\.cache\torch"
  ```

### Performance Optimization
- Close browser tabs when processing
- Close other GPU applications (games, video editing)
- Use Maximum quality only for final production, test with Balanced first
- Enable Windows Game Mode for stable GPU clocks

### Environment Management
- Keep environments isolated (don't mix packages)
- Document any custom installations
- Back up working environments before major updates

---

## 🆘 Still Having Issues?

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Verify all prerequisites are correctly installed
3. Try reinstalling in a fresh directory
4. Check GitHub Issues for similar problems
5. Open a new issue with:
   - Windows version
   - Python version (`python --version`)
   - CUDA version (`nvcc --version`)
   - GPU model
   - Full error message/traceback

---

**Next Steps**: See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for usage instructions!
