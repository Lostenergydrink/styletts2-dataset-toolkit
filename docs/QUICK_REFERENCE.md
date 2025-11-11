# ⚡ Quick Reference

Fast lookup for common commands and workflows.

---

## 🚀 Launch Commands

### Stem Separation
```powershell
cd stem-separation
.\launch_stem_separation.bat
```
**URL**: http://127.0.0.1:7861

### StyleTTS2
```powershell
cd styletts2-setup
.\launch_styletts2.bat
```
**URL**: http://localhost:7860

---

## 🎛️ Quality Presets

| Preset | Time | Quality | Use For |
|--------|------|---------|---------|
| Fast | 20s/min | Good | Testing |
| Balanced | 40s/min | Very Good | General |
| High Quality | 90s/min | Excellent | Production |
| Maximum ⭐ | 2-3min/min | Outstanding | Voice Cloning |

**Recommendation**: Always use **Maximum** for voice cloning!

---

## 📁 Key Directories

```
stem-outputs/          # Separated vocals
training-data/         # Raw and processed audio
  ├── raw/            # Original uploads
  ├── processed/      # Segmented 24kHz WAV
  └── transcripts/    # Whisper transcriptions
datasets/             # Exported training datasets
models/               # Trained voice models
```

---

## 🔧 Common Tasks

### Batch Separate Vocals
1. Go to "📦 Batch Processing" tab
2. Enter folder path
3. Select `htdemucs_ft` + `Maximum (Slow)`
4. Check "Vocals Only"
5. Click "Start Batch Processing"

### Prepare Dataset
1. "1️⃣ Import Audio" → Upload files
2. "2️⃣ Segment Audio" → 60s chunks
3. "3️⃣ Transcribe" → Use `base` model
4. "4️⃣ Export Dataset" → Name your dataset
5. "5️⃣ View Datasets" → Verify quality

### Train Model
```powershell
cd E:\AI\StyleTTS2
python train_finetune.py --config_path ./Configs/config_ft.yml
```

---

## 🐛 Quick Troubleshooting

### CUDA Not Available
```powershell
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Out of Memory
- Use lower quality preset
- Reduce batch_size in training config
- Close other GPU applications

### FFmpeg Not Found
```powershell
# Add to PATH or update launcher scripts
$env:PATH = "E:\AI\tools\ffmpeg\bin;$env:PATH"
```

---

## 📊 Dataset Requirements

| Quality | Duration | Samples | Training Time |
|---------|----------|---------|---------------|
| Minimum | 30 min | 30+ clips | ~2 hours |
| Good | 1 hour | 60+ clips | ~4 hours |
| Excellent | 4+ hours | 240+ clips | ~16 hours |

---

## 🎯 Best Practices

✅ **DO:**
- Use Maximum quality for final datasets
- Test with small subset first
- Verify transcriptions
- Keep vocals-only for training
- Use 24kHz WAV format

❌ **DON'T:**
- Skip stem separation
- Use low-quality source audio
- Train on <30 minutes
- Mix multiple speakers
- Use heavily compressed audio

---

## 🔑 Keyboard Shortcuts (Windows)

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Stop server |
| `Ctrl+Shift+Esc` | Task Manager (check GPU) |
| `Win+R` → `nvidia-smi` | Check GPU status |

---

## 📞 Quick Links

- [Full Installation](docs/INSTALLATION.md)
- [Complete Workflow](docs/WORKFLOW_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Dataset Guide](docs/DATASET_PREP_GUIDE.md)

---

## 💡 Tips

1. **Process overnight** for large batches
2. **Save checkpoints** every 5-10 epochs
3. **Test early epochs** (20-30) before waiting for 50+
4. **Monitor VRAM** with `nvidia-smi`
5. **Clear cache** between big jobs: `torch.cuda.empty_cache()`

---

## 🆘 Emergency Fixes

### Everything Broken
```powershell
# Nuclear option - reinstall everything
Remove-Item -Recurse -Force stem-separation\venv
Remove-Item -Recurse -Force styletts2-setup\.venv
.\install.ps1
```

### GPU Not Detected
```powershell
# Check driver
nvidia-smi

# Reinstall PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Port Already in Use
```powershell
# Kill process on port 7861
Get-Process -Id (Get-NetTCPConnection -LocalPort 7861).OwningProcess | Stop-Process
```

---

**Keep this handy! 📌**
