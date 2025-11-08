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

#### 3.2 Segment Audio
1. Go to **2️⃣ Segment Audio**
2. Select your speaker
3. Set chunk duration (60 seconds recommended)
4. Click **Segment**

This will:
- Convert all audio to 24kHz mono WAV
- Split into ~1 minute chunks
- Save to `training-data/processed/[speaker_name]/`

📊 **Check duration** - aim for 30 mins minimum!

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

#### 3.4 Export Dataset
1. Go to **4️⃣ Export Dataset**
2. Select your speaker
3. Enter dataset name (e.g., `morgan_freeman_dataset`)
4. Click **Export**

Creates StyleTTS2-compatible dataset:
- Format: `filename.wav|transcription|speaker`
- Location: `datasets/[dataset_name]/`
- Includes `train_list.txt` filelist

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

# Download pretrained LibriTTS model
# From: https://huggingface.co/yl4579/StyleTTS2-LibriTTS/tree/main
# Place in: StyleTTS2/Models/LibriTTS/
```

### Configure Training

1. **Copy your dataset** to StyleTTS2 folder:
   ```bash
   cp -r E:/AI/tts-webui/styletts2/datasets/your_dataset StyleTTS2/Data/
   ```

2. **Edit `Configs/config_ft.yml`**:
   ```yaml
   # Update these paths
   train_data: Data/your_dataset/train_list.txt
   val_data: Data/your_dataset/train_list.txt  # Use same for simplicity
   
   # Adjust batch size for your GPU (RTX 3060 12GB)
   batch_size: 4
   
   # Training epochs (50-100 recommended)
   epochs: 50
   ```

3. **Start fine-tuning**:
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

- Check TensorBoard logs: `log_dir/`
- Watch for loss convergence
- Test checkpoints periodically

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

**"Out of memory" during training:**
- Reduce `batch_size` in config
- Reduce `max_len` parameter
- Close other GPU applications

**"Loss becomes NaN":**
- Ensure batch_size >= 4
- Check audio quality (corrupted files?)
- Try disabling mixed precision

**Poor quality output:**
- Dataset too small (need more data)
- Transcripts inaccurate (review manually)
- Audio quality inconsistent (redo stem separation)

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
