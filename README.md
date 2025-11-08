# 🎤 StyleTTS2 Dataset Toolkit

**Complete Windows-optimized workflow for voice cloning with StyleTTS2**

A comprehensive toolkit for isolating vocals, preparing datasets, and fine-tuning StyleTTS2 voice models. Optimized for Windows with GPU acceleration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CUDA](https://img.shields.io/badge/CUDA-12.1+-green.svg)](https://developer.nvidia.com/cuda-downloads)

---

## 🌟 Features

### 🎵 Stem Separation (Enhanced)
- **Quality presets**: Fast / Balanced / High Quality / Maximum (Slow)
- **Batch processing** from Gradio UI
- **Aggressive vocal isolation** optimized for voice cloning
- **Multiple models**: Demucs v4 (htdemucs_ft, htdemucs_6s) & UVR models
- **Model caching** for faster processing
- **GPU-accelerated** with VRAM management

### 🗣️ StyleTTS2 Integration
- Clean setup with isolated virtual environment
- Dataset preparation pipeline (import → segment → transcribe → export)
- Launcher scripts for Windows
- FFmpeg integration

### 📦 Complete Pipeline
```
Raw Audio → Stem Separation → Dataset Prep → StyleTTS2 Training → Custom Voice
```

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11**
- **Python 3.10+**
- **NVIDIA GPU** with CUDA support (12GB+ VRAM recommended)
- **FFmpeg** (for audio processing)

### Installation

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions.

**Quick version:**
```powershell
# 1. Clone repository
git clone https://github.com/Lostenergydrink/styletts2-dataset-toolkit.git
cd styletts2-dataset-toolkit

# 2. Install stem separation
cd stem-separation
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 3. Install StyleTTS2
cd ../styletts2-setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install styletts2 gradio
```

---

## 🎯 Usage Workflow

### Step 1: Extract Clean Vocals 🎤

Launch the stem separation web UI:
```powershell
cd stem-separation
.\launch_stem_separation.bat
```

**For Single Files:**
1. Go to "🔥 Demucs (Best Quality)" tab
2. Upload your audio file
3. Select model: `htdemucs_ft`
4. Select quality: `Maximum (Slow)` ⭐ **Recommended for voice cloning**
5. Click "Separate Stems"
6. Download the vocals stem

**For Batch Processing:**
1. Go to "📦 Batch Processing" tab
2. Enter folder path (e.g., `C:\Users\YourName\Music\Recordings`)
3. Select quality: `Maximum (Slow)`
4. Check "Vocals Only"
5. Click "Start Batch Processing"
6. Outputs saved to: `stem-outputs/batch/[folder-name]/htdemucs_ft/`

**Quality Comparison:**
- **Fast**: ~15-20s per minute of audio, good for testing
- **Balanced**: ~30-40s per minute, general purpose
- **High Quality**: ~60-90s per minute, great results
- **Maximum (Slow)**: ~2-3 min per minute of audio, **best quality for voice cloning** ⭐

### Step 2: Prepare Dataset for Training 📊

Launch StyleTTS2 web UI:
```powershell
cd styletts2-setup
.\launch_styletts2.bat
```

Follow the dataset preparation pipeline in the **Dataset Prep & Training** tab:

1. **Import Audio** → Upload your clean vocal files
2. **Segment Audio** → Split into ~1 minute chunks
3. **Transcribe** → Auto-generate transcripts with Whisper
4. **Export Dataset** → Create training-ready dataset
5. **Verify** → Check dataset quality and duration

**Recommended Dataset Sizes:**
- 30 minutes minimum
- 1-2 hours for great quality
- 4+ hours for excellent quality

### Step 3: Fine-Tune Voice Model 🎓

See [docs/DATASET_PREP_GUIDE.md](docs/DATASET_PREP_GUIDE.md) for complete training instructions.

---

## 📁 Repository Structure

```
styletts2-dataset-toolkit/
├── stem-separation/
│   ├── stem_separation_webui.py    # Enhanced Gradio UI
│   ├── batch_separate.py            # Standalone batch script
│   ├── launch_stem_separation.bat   # Windows launcher
│   ├── requirements.txt             # Dependencies
│   └── QUALITY_PRESETS.md           # Quality settings explained
│
├── styletts2-setup/
│   ├── launch_styletts2.bat         # StyleTTS2 launcher
│   ├── launch_styletts2.ps1         # PowerShell launcher
│   └── STYLETTS2_README.md          # StyleTTS2 setup guide
│
├── docs/
│   ├── INSTALLATION.md              # Detailed installation guide
│   ├── WORKFLOW_GUIDE.md            # Step-by-step workflow
│   ├── DATASET_PREP_GUIDE.md        # Dataset preparation & training
│   └── TROUBLESHOOTING.md           # Common issues & solutions
│
└── examples/
    └── screenshots/                 # UI screenshots and examples
```

---

## 💡 Why This Toolkit?

### Windows-First Design
Most ML voice cloning tools assume Linux. This toolkit is built for Windows users with:
- Batch launchers (`.bat` files)
- PowerShell scripts
- Windows path handling
- GPU optimization for Windows

### Quality-Focused
- **Maximum quality presets** specifically for voice cloning (not just music separation)
- Test-time augmentation (shifts=2) for cleaner vocals
- Higher overlap (0.75) to eliminate artifacts
- Model caching for efficiency

### Complete Pipeline
- End-to-end workflow from raw audio to trained model
- Integrated Gradio UI for both stem separation and StyleTTS2
- Batch processing for large datasets
- No terminal commands required (GUI-driven)

### Beginner-Friendly
- Clear documentation with examples
- Automated launchers
- Progress indicators and status messages
- Troubleshooting guides

---

## 🛠️ Technical Details

### Stem Separation
- **Backend**: Demucs v4 (Meta AI), UVR models
- **Models**: htdemucs_ft (best quality), htdemucs_6s (6 stems)
- **Quality Settings**: Configurable overlap, splitting, and shifts
- **Performance**: GPU-accelerated with PyTorch
- **Optimizations**: Model caching, VRAM management, TF32 precision

### StyleTTS2
- **Architecture**: Diffusion-based TTS with style encoder
- **Pre-trained**: LibriTTS model
- **Fine-tuning**: Compatible with official training scripts
- **Features**: Voice cloning, style transfer, prosody control

### System Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 2060 (6GB) | RTX 3060+ (12GB) |
| RAM | 8GB | 16GB+ |
| Storage | 10GB | 50GB+ |
| Python | 3.10 | 3.10 or 3.11 |

### Performance Benchmarks (RTX 3060 12GB)
| Task | Speed |
|------|-------|
| Stem Separation (Maximum) | ~2-3 min per min of audio |
| Batch Processing (10 files) | ~20-30 min |
| Transcription (Whisper base) | ~10-30 sec per min of audio |
| Training (1 hour dataset) | ~4 hours |

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional stem separation models
- Training automation
- Multi-GPU support
- Linux/Mac compatibility
- UI enhancements

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Acknowledgments & Credits

This toolkit builds upon these excellent open-source projects:

- **[Demucs](https://github.com/facebookresearch/demucs)** by Meta AI - State-of-the-art music source separation (MIT License)
- **[StyleTTS2](https://github.com/yl4579/StyleTTS2)** - High-quality text-to-speech synthesis (MIT License)
- **[Audio Separator](https://github.com/nomadkaraoke/python-audio-separator)** - UVR model integration (MIT License)
- **[Gradio](https://gradio.app/)** - Easy-to-use web interfaces (Apache 2.0 License)
- **[Whisper](https://github.com/openai/whisper)** by OpenAI - Automatic speech recognition (MIT License)

Thank you to all the researchers and developers who made this toolkit possible!

---

## 🔗 Resources

### Documentation
- [Installation Guide](docs/INSTALLATION.md)
- [Workflow Guide](docs/WORKFLOW_GUIDE.md)
- [Dataset Prep Guide](docs/DATASET_PREP_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Related Projects
- [Demucs GitHub](https://github.com/facebookresearch/demucs)
- [StyleTTS2 GitHub](https://github.com/yl4579/StyleTTS2)
- [StyleTTS2 Fine-tuning Discussion](https://github.com/yl4579/StyleTTS2/discussions/128)

### Community
- Report bugs: [GitHub Issues](https://github.com/Lostenergydrink/styletts2-dataset-toolkit/issues)
- Request features: [GitHub Discussions](https://github.com/Lostenergydrink/styletts2-dataset-toolkit/discussions)

---

## 📊 Changelog

### v1.0.0 (November 2025)
- Initial release
- Enhanced stem separation with quality presets
- Batch processing from Gradio UI
- StyleTTS2 integration
- Complete documentation
- Windows-optimized setup

---

## ⭐ Star History

If this toolkit helped you create amazing voice models, please consider starring the repository!

---

**Made with ❤️ for the voice cloning community**

*Perfect for voice actors, content creators, researchers, and AI enthusiasts*
