# 🔧 Troubleshooting Guide

Common issues and solutions for the StyleTTS2 Dataset Toolkit.

---

## 🎵 Stem Separation Issues

### Web UI won't start

**Symptoms:**
- `launch_stem_separation.bat` fails
- Browser doesn't open
- Import errors

**Solutions:**

1. **Check virtual environment:**
   ```powershell
   cd stem-separation
   .\venv\Scripts\Activate.ps1
   python -c "import torch, demucs, gradio; print('All modules OK')"
   ```

2. **Reinstall dependencies:**
   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```

3. **Check port availability:**
   ```powershell
   netstat -ano | findstr :7861
   ```
   If port 7861 is in use, kill the process or edit `stem_separation_webui.py` to use different port.

### "CUDA out of memory" during separation

**Symptoms:**
- Processing fails midway
- `RuntimeError: CUDA out of memory`

**Solutions:**

1. **Close other GPU applications** (browsers with hardware acceleration, games, etc.)

2. **Use lower quality preset:**
   - Switch from `Maximum` to `High Quality` or `Balanced`

3. **Process shorter files:**
   - Split long files into chunks before processing

4. **Reduce VRAM usage in code:**
   Edit `stem_separation_webui.py`:
   ```python
   # Change split=False to split=True
   sources = apply_model(model, wav.unsqueeze(0), device=device, 
                        split=True, overlap=overlap, shifts=shifts)[0]
   ```

### Poor vocal isolation quality

**Symptoms:**
- Vocals have music bleed
- Artifacts/warbling sounds
- Muffled vocals

**Solutions:**

1. **Try different model:**
   - `htdemucs_ft` → `htdemucs_6s`
   - Or try UVR models tab

2. **Check source quality:**
   - Source audio might be too compressed
   - Try different source if available

3. **Use different quality preset:**
   - Sometimes `High Quality` works better than `Maximum`
   - Test both and compare

4. **Post-processing:**
   - Use noise reduction (Audacity, RX, etc.)
   - Manual cleanup for critical sections

### Batch processing fails on some files

**Symptoms:**
- Some files processed successfully
- Others fail with errors

**Solutions:**

1. **Check file formats:**
   - Ensure all files are valid audio
   - Convert problematic files:
     ```powershell
     ffmpeg -i problematic.mp3 -ar 44100 fixed.wav
     ```

2. **Check file names:**
   - Avoid special characters in filenames
   - Use only alphanumeric and underscores

3. **Process failed files individually:**
   - Use single-file processing to see specific errors

---

## 🗣️ StyleTTS2 Issues

### Model loading errors

**Symptoms:**
- "Failed to load model"
- Import errors
- Model not found

**Solutions:**

1. **Check installation:**
   ```powershell
   cd styletts2-setup
   .\.venv\Scripts\Activate.ps1
   python -c "import styletts2; print('OK')"
   ```

2. **Reinstall StyleTTS2:**
   ```powershell
   pip uninstall styletts2
   pip install styletts2
   ```

3. **Check model paths:**
   - Ensure models exist in `models/` directory
   - Download manually if needed from Hugging Face

### Transcription failures

**Symptoms:**
- Whisper fails to transcribe
- Empty transcripts
- Memory errors

**Solutions:**

1. **Use smaller Whisper model:**
   - Switch from `medium` → `base` → `tiny`

2. **Process in smaller batches:**
   - Reduce chunk duration in segmentation

3. **Check audio format:**
   - Ensure files are valid WAV
   - Resample to 16kHz: `ffmpeg -i input.wav -ar 16000 output.wav`

4. **Reinstall Whisper:**
   ```powershell
   pip uninstall openai-whisper
   pip install openai-whisper
   ```

### "Invalid or missing model checkpoint"

**Symptoms:**
- Console shows "Loading default model"
- Want to use custom model

**Solutions:**

1. **Check model path** in config
2. **Ensure model file exists** and is not corrupted
3. **Use absolute paths** in config
4. **Default models work fine** for initial use

### Dataset export fails

**Symptoms:**
- Export button doesn't work
- Files not created

**Solutions:**

1. **Check disk space** (need ~2x audio size)

2. **Check permissions:**
   - Ensure write access to `datasets/` folder

3. **Try different dataset name:**
   - Avoid special characters

4. **Check logs** for specific errors

---

## 🎓 Training Issues

### "CUDA out of memory" during training

**Symptoms:**
- Training crashes
- `RuntimeError: CUDA out of memory`

**Solutions:**

1. **Reduce batch size** in `config_ft.yml`:
   ```yaml
   batch_size: 2  # Was 4
   ```

2. **Reduce max_len:**
   ```yaml
   max_len: 300  # Was 400
   ```

3. **Enable gradient checkpointing:**
   ```yaml
   gradient_checkpointing: true
   ```

4. **Close other GPU apps** before training

### Training loss becomes NaN

**Symptoms:**
- Loss shows as `nan`
- Training becomes unstable

**Solutions:**

1. **Reduce learning rate:**
   ```yaml
   lr: 0.00005  # Was 0.0001
   ```

2. **Check dataset quality:**
   - Remove corrupted audio files
   - Verify transcripts match audio

3. **Ensure batch_size >= 4:**
   ```yaml
   batch_size: 4  # Minimum
   ```

4. **Use gradient clipping:**
   ```yaml
   grad_clip: 1.0
   ```

### Poor model quality after training

**Symptoms:**
- Generated speech sounds unnatural
- Voice doesn't match training data
- Artifacts in output

**Solutions:**

1. **Train longer:**
   - Increase epochs: 50 → 100

2. **More training data:**
   - Need 1+ hour minimum
   - 4+ hours for best quality

3. **Improve dataset quality:**
   - Better stem separation
   - Manual transcript review
   - Remove poor quality samples

4. **Adjust training parameters:**
   ```yaml
   lr: 0.0001  # Experiment
   epochs: 100
   batch_size: 4
   ```

5. **Try different checkpoints:**
   - Test epochs 20, 30, 40, 50
   - Earlier might sound better (before overfitting)

---

## 🖥️ System Issues

### Python/pip not found

**Symptoms:**
- `'python' is not recognized`
- `'pip' is not recognized`

**Solutions:**

1. **Add Python to PATH:**
   - Windows Search → "Environment Variables"
   - Edit PATH
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\`
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\Scripts\`

2. **Restart PowerShell** after PATH changes

3. **Use full path:**
   ```powershell
   C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe --version
   ```

### FFmpeg not found

**Symptoms:**
- "FFmpeg is required"
- Audio conversion fails

**Solutions:**

1. **Install FFmpeg:**
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract to: `E:\AI\tools\ffmpeg\`

2. **Add to PATH:**
   - Add: `E:\AI\tools\ffmpeg\bin`
   - Restart PowerShell

3. **Update launcher scripts** with correct FFmpeg path

4. **Test:**
   ```powershell
   ffmpeg -version
   ```

### CUDA not detected

**Symptoms:**
- `torch.cuda.is_available()` returns `False`
- Processing uses CPU (very slow)

**Solutions:**

1. **Check NVIDIA driver:**
   ```powershell
   nvidia-smi
   ```
   Should show GPU info. If not, update drivers.

2. **Install CUDA Toolkit:**
   - Download: https://developer.nvidia.com/cuda-downloads
   - Install CUDA 12.1+

3. **Reinstall PyTorch with CUDA:**
   ```powershell
   pip uninstall torch torchaudio
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

4. **Verify:**
   ```powershell
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Disk space issues

**Symptoms:**
- "No space left on device"
- Installation fails
- Processing fails

**Solutions:**

1. **Check free space:**
   ```powershell
   Get-PSDrive
   ```

2. **Move to larger drive:**
   - Move entire toolkit to E: or D: drive

3. **Clean up:**
   - Delete old outputs: `stem-outputs/`
   - Delete unused models
   - Clear cache: `pip cache purge`

4. **Set cache locations:**
   ```powershell
   $env:HF_HOME = "E:\AI\.cache\huggingface"
   $env:TORCH_HOME = "E:\AI\.cache\torch"
   $env:PIP_CACHE_DIR = "E:\AI\.cache\pip"
   ```

---

## 🌐 Network Issues

### Model downloads fail

**Symptoms:**
- Timeout errors
- Connection refused
- Slow downloads

**Solutions:**

1. **Use VPN** if in restricted region

2. **Download manually:**
   - Get models from Hugging Face
   - Place in cache directories

3. **Use mirror sites:**
   ```python
   # Edit code to use mirror
   os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
   ```

4. **Retry with timeout increase:**
   ```python
   import torch
   torch.hub.set_dir('E:/AI/.cache/torch')
   ```

---

## 🪟 Windows-Specific Issues

### PowerShell execution policy

**Symptoms:**
- "cannot be loaded because running scripts is disabled"
- `.ps1` files won't run

**Solutions:**

1. **Run as Administrator:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Or bypass temporarily:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File script.ps1
   ```

### Long path issues

**Symptoms:**
- "Path too long"
- File operations fail

**Solutions:**

1. **Enable long paths in Windows:**
   - Run as Administrator:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
   -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

2. **Use shorter paths:**
   - Move to `E:\toolkit\` instead of deep nested folders

### Antivirus interference

**Symptoms:**
- Files disappear
- Scripts blocked
- Slow performance

**Solutions:**

1. **Add exclusions** for:
   - `E:\styletts2-dataset-toolkit\`
   - Python installation directory
   - CUDA directories

2. **Temporarily disable** during installation

---

## 📊 Performance Issues

### Very slow processing

**Symptoms:**
- Processing takes much longer than expected
- GPU utilization low

**Solutions:**

1. **Check GPU usage:**
   ```powershell
   nvidia-smi
   ```
   Should show 80-100% GPU utilization.

2. **Ensure CUDA is used:**
   ```python
   print(torch.cuda.is_available())  # Should be True
   print(torch.cuda.current_device())  # Should show GPU
   ```

3. **Close background apps:**
   - Browser tabs
   - Other GPU applications

4. **Use lower quality preset** if still slow

### High RAM usage

**Symptoms:**
- System becomes unresponsive
- Out of memory errors

**Solutions:**

1. **Process in smaller batches**

2. **Close other applications**

3. **Increase page file size:**
   - Windows Settings → System → About → Advanced system settings
   - Performance → Settings → Advanced → Virtual memory

4. **Add more RAM** if consistently hitting limits

---

## 🐛 Debug Techniques

### Enable verbose logging

Edit scripts to add debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check CUDA details

```python
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"CUDA Version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
```

### Test individual components

```python
# Test Demucs
from demucs.pretrained import get_model
model = get_model('htdemucs_ft')
print("Demucs OK")

# Test StyleTTS2
import styletts2
print("StyleTTS2 OK")

# Test Whisper
import whisper
model = whisper.load_model("base")
print("Whisper OK")
```

---

## 🆘 Getting Help

If issues persist:

1. **Check documentation:**
   - [INSTALLATION.md](INSTALLATION.md)
   - [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)

2. **Search GitHub Issues:**
   - [StyleTTS2 Issues](https://github.com/yl4579/StyleTTS2/issues)
   - [Demucs Issues](https://github.com/facebookresearch/demucs/issues)

3. **Open new issue** with:
   - Windows version
   - Python version
   - GPU model
   - CUDA version
   - Full error message/traceback
   - Steps to reproduce

4. **Join communities:**
   - Reddit: r/MachineLearning, r/LocalLLaMA
   - Discord: AI Voice Cloning servers

---

## 📝 Reporting Bugs

When reporting issues, include:

```
### System Info
- OS: Windows 11
- Python: 3.10.6
- GPU: RTX 3060 12GB
- CUDA: 12.1

### Issue
[Clear description]

### Steps to Reproduce
1. ...
2. ...

### Error Message
```
[Full traceback]
```

### Expected Behavior
[What should happen]

### Additional Context
[Screenshots, logs, etc.]
```

---

**Most issues are fixable! Don't give up! 💪**
