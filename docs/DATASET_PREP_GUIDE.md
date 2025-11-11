# 🎓 StyleTTS2 Dataset Preparation & Fine-Tuning Guide

## 📋 Overview

This guide walks you through preparing a dataset and fine-tuning StyleTTS2 for superior voice quality with your custom speaker.

## 🎯 Quality Expectations

| Dataset Size | Expected Quality |
|--------------|-----------------|
| 30 minutes   | Good quality, recognizable voice |
| 1-2 hours    | Great quality, natural speech |
| 4+ hours     | Excellent quality, near-perfect replication |

## 📝 Workflow

### Step 1: Collect Audio 🎵

**Sources:**
- YouTube videos/podcasts
- Audiobooks
- Interviews
- Any clean speech recordings

**Recommendations:**
- Use **stem separation** first to isolate vocals
- Aim for clean, consistent audio quality
- Avoid heavy background music or noise
- Multiple shorter clips are better than one long clip

### Step 2: Prepare Audio Files

1. **Extract audio** from videos (if needed):
   ```bash
   ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3
   ```

2. **Stem separation** (HIGHLY RECOMMENDED):
   - Launch: `E:\AI\stem-separation-webui\launch_stem_separation.bat`
   - Use **Demucs (htdemucs_ft)** model
   - Extract isolated vocals
   - This dramatically improves training quality!

3. **Convert to common format** (MP3, WAV, FLAC, M4A all supported)

### Step 3: Use the WebUI Pipeline

#### 3.1 Import Audio
1. Open StyleTTS2 WebUI → **Dataset Prep & Training** tab
2. Go to **1️⃣ Import Audio**
3. Enter speaker name (e.g., `morgan_freeman`)
4. Select all your audio files
5. Click **Import**

📁 Files saved to: `training-data/raw/[speaker_name]/`

#### 3.2 Segment Audio ⚠️ **UPDATED - SAFE LIMITS**
1. Go to **2️⃣ Segment Audio**
2. Select your speaker
3. Set chunk duration:
   - **Range:** 3-30 seconds (hard limit to prevent BERT token overflow)
   - **Default:** 10 seconds (recommended - keeps transcripts under 450 chars)
   - **Why shorter?** StyleTTS2 has a 512 BERT token limit (~450 char safe limit)
4. Click **Segment**

This will:
- Convert all audio to 24kHz mono WAV
- Split into short chunks (safe for training)
- Save to `training-data/processed/[speaker_name]/`

📊 **Check duration** - aim for 30 mins minimum!

⚠️ **Important:** The slider range has been updated from 30-90 seconds to 3-30 seconds to prevent transcript length issues during training.

#### 3.3 Transcribe
1. Go to **3️⃣ Transcribe**
2. Select your speaker
3. Choose Whisper model:
   - `base` - Good balance (recommended)
   - `small` - Better accuracy, slower
   - `medium` - High quality, much slower
4. Click **Transcribe**

GPU-accelerated transcription will:
- Process all audio chunks
- Generate accurate transcripts
- Save to `training-data/transcripts/[speaker_name]/`

⏱️ Time: ~10-30 seconds per minute of audio (on RTX 3060)

**Note:** Whisper may produce digits and symbols in transcripts. This is expected and will be fixed automatically in the next step.

#### 3.4 Export Dataset ✨ **NOW WITH AUTO-NORMALIZATION**
1. Go to **4️⃣ Export Dataset**
2. Select your speaker
3. Enter dataset name (e.g., `morgan_freeman_dataset`)
4. Click **Export**

**The export process now automatically:**
- ✅ Converts digits to words ("25%" → "twenty five percent")
- ✅ Removes unsupported characters (hyphens, special symbols)
- ✅ Truncates overly long transcripts at sentence boundaries
- ✅ Validates against 178-token vocabulary
- ✅ Shows detailed warnings for any issues

**You no longer need to manually run normalization scripts!**

Creates StyleTTS2-compatible dataset:
- Format: `filename.wav|transcription|0`
- Location: `datasets/[dataset_name]/`
- Includes `train_list.txt` manifest file

**Example Export Output:**
```
✅ Dataset exported successfully!

Dataset: morgan_freeman_v2
Files: 156 audio + transcript pairs

🔧 Normalization applied to 23 transcripts:
   - Converted digits to words
   - Removed unsupported characters
   - Truncated overly long text
   - Total warnings: 47

🎓 Ready for fine-tuning!
```

#### 3.5 Verify Dataset
1. Go to **5️⃣ View Datasets**
2. Select your dataset
3. Review information:
   - Total samples
   - Duration
   - Sample entries

✅ **You're ready to fine-tune!**

## 🎓 Fine-Tuning (External Training)

### Prerequisites

```bash
# Clone StyleTTS2 repository
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2

# Install requirements
pip install -r requirements.txt

# Install TensorBoard for training monitoring
pip install tensorboard

# Download pretrained LibriTTS model
# From: https://huggingface.co/yl4579/StyleTTS2-LibriTTS/tree/main
# Place in: StyleTTS2/Models/LibriTTS/
```

### Configure Training

1. **Split your dataset into train and validation sets:**
   
   **⚠️ IMPORTANT:** You MUST create separate train_list.txt and val_list.txt files. Do NOT reuse the same file for both!
   
   ```powershell
   # Example: Split 156 samples into 140 train + 16 val (90/10 split)
   cd datasets/your_dataset
   
   # Create training set (first 140 lines)
   Get-Content train_list.txt | Select-Object -First 140 > train_list_split.txt
   
   # Create validation set (last 16 lines)
   Get-Content train_list.txt | Select-Object -Last 16 > val_list.txt
   
   # Replace original with split version
   Move-Item train_list_split.txt train_list.txt -Force
   ```

2. **Copy your dataset** to StyleTTS2 folder:
   ```bash
   cp -r styletts2-dataset-toolkit/datasets/your_dataset StyleTTS2/Data/
   ```

3. **Edit `Configs/config_ft.yml`**:
   ```yaml
   # Device configuration (auto detects CUDA or falls back to CPU)
   device: "auto"  # or "cuda" or "cpu"
   
   # Data paths - MUST be separate files!
   data_params:
     train_data: Data/your_dataset/train_list.txt
     val_data: Data/your_dataset/val_list.txt  # Different file!
     root_path: Data/your_dataset
   
   # Windows-specific: must use num_workers=0 to prevent process spawning issues
   loader_params:
     train_num_workers: 0
     val_num_workers: 0
   
   # Adjust batch size for your GPU (RTX 3060 12GB)
   batch_size: 4  # Reduce to 2 if OOM errors occur
   
   # Training epochs (50-100 recommended)
   epochs: 50
   ```

4. **Apply code patches** (if not already done):
   
   See the `styletts2-setup/patches/` directory for modified StyleTTS2 files that fix:
   - Device compatibility (CPU/CUDA auto-detection)
   - Windows DataLoader issues (num_workers=0)
   - Vocabulary constraints (mask_from_lens fallback)
   
   Use the `apply_patches.ps1` script to apply these automatically.

5. **Start fine-tuning**:
   ```bash
   python train_finetune.py --config_path ./Configs/config_ft.yml
   ```

### Training Time

| Dataset Size | Training Time (RTX 3060) |
|--------------|-------------------------|
| 30 mins      | ~2 hours |
| 1 hour       | ~4 hours |
| 4 hours      | ~12-16 hours |

### Monitor Training

- **Watch console output** for loss convergence
- **TensorBoard** (optional but recommended):
  ```bash
  tensorboard --logdir=log_dir
  # Open: http://localhost:6006
  ```
- **Test checkpoints** periodically (epochs 20, 30, 40, 50)

### Using Your Fine-Tuned Model

After training:

1. **Copy model checkpoint**:
   ```bash
   cp epoch_2nd_00050.pth E:/AI/tts-webui/styletts2/models/finetuned/your_model.pth
   ```

2. **Load in webui** (future feature - coming soon!)

## 💡 Pro Tips

### Audio Quality
- ✅ Clean, isolated vocals (use stem separation!)
- ✅ Consistent recording environment
- ✅ Clear speech, minimal mumbling
- ✅ Natural speaking pace
- ❌ Avoid music/noise in background
- ❌ Avoid heavily processed audio
- ❌ Avoid multiple speakers talking

### Dataset Balance
- Aim for diverse sentence structures
- Include various emotions/tones if present in source
- Ensure transcripts are accurate (review samples!)

### Training Tips
- Start with 30-60 minutes first to test
- Monitor GPU memory (reduce batch_size if OOM)
- Save checkpoints regularly
- Test early checkpoints (~epoch 20) for quality

### Common Issues

**"Index out of range in gather" or vocabulary mismatch errors:**
- **Cause:** Transcripts contain digits or unsupported characters
- **Solution:** ~~Run `normalize_dataset.py`~~ **FIXED:** Export step now auto-normalizes
- **Prevention:** Use the updated WebUI which handles this automatically
- **Manual fix:** If you manually edited transcripts, run:
  ```powershell
  python styletts2-setup/normalize_dataset.py datasets/your-dataset/train_list.txt --apply
  ```

**"Expanded size of tensor (646) must match existing size (512)" - BERT token limit:**
- **Cause:** Transcript too long (>450 chars, exceeds 512 BERT token limit)
- **Solution 1 (Best):** Re-segment audio shorter in Step 2 (use 10-15 sec chunks)
- **Solution 2 (Automatic):** Export step will truncate at sentence boundary
- **Solution 3 (Manual):** Run `normalize_dataset.py` if you manually edited transcripts
- **Prevention:** Use slider values 3-30 seconds (new WebUI enforces this)

**"Out of memory" during training:**
- Reduce `batch_size` in config (try 4, then 2, then 1)
- Reduce `max_len` parameter
- Close other GPU applications
- Check VRAM usage with `nvidia-smi`

**"Loss becomes NaN":**
- Ensure batch_size >= 4 (or >= 2 if using small dataset)
- Check audio quality (corrupted files?)
- Validate dataset with `validate_dataset.py`
- Try disabling mixed precision

**"srcIndex < srcSelectDimSize" - CUDA device errors:**
- **Cause:** Hardcoded CUDA calls in training code
- **Solution:** Use patched training files from `styletts2-setup/patches/`
- **Config:** Set `device: "auto"` in config_ft.yml

**Windows DataLoader spawning many console windows:**
- **Cause:** `num_workers > 0` causes process fork bomb on Windows
- **Solution:** Set `num_workers: 0` in config under `loader_params`
- **Patched:** The updated code forces this automatically on Windows

**Poor quality output:**
- Dataset too small (need 30+ minutes, 1-2 hours recommended)
- Transcripts inaccurate (run `validate_dataset.py` to check)
- Audio quality inconsistent (redo stem separation with "Maximum" quality)
- Vocabulary mismatch (check for digits/symbols in transcripts)

**Training validation errors / division by zero:**
- **Cause:** Reusing train_list.txt for validation
- **Solution:** Create separate val_list.txt file (see train/val split section above)

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [DATASET_REQUIREMENTS.md](DATASET_REQUIREMENTS.md).

## 📚 Resources

- **StyleTTS2 Repo**: https://github.com/yl4579/StyleTTS2
- **Fine-tuning Guide**: https://github.com/yl4579/StyleTTS2/discussions/128
- **Common Issues**: https://github.com/yl4579/StyleTTS2/discussions/81
- **Pretrained Models**: https://huggingface.co/yl4579/StyleTTS2-LibriTTS

## 🎉 Workflow Summary

```
Raw Audio Files
    ↓
Stem Separation (vocals only)
    ↓
Import to WebUI
    ↓
Segment (1min chunks, 24kHz WAV)
    ↓
Transcribe with Whisper
    ↓
Export Dataset (StyleTTS2 format)
    ↓
Fine-tune with train_finetune.py
    ↓
🎊 Custom High-Quality Voice Model!
```

## 📁 Directory Structure

```
tts-webui/styletts2/
├── training-data/
│   ├── raw/               ← Your imported audio
│   │   └── speaker_name/
│   ├── processed/         ← Segmented 24kHz WAV
│   │   └── speaker_name/
│   └── transcripts/       ← Whisper transcriptions
│       └── speaker_name/
├── datasets/              ← Exported training datasets
│   └── dataset_name/
│       ├── *.wav
│       └── train_list.txt
└── models/
    ├── base/              ← StyleTTS2 default models
    └── finetuned/         ← Your custom models
        └── your_model.pth
```

---

**Happy training! You're about to create some amazing custom voices! 🎤✨**
