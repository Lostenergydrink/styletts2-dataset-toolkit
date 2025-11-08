# 🎬 Complete Workflow Guide

Step-by-step guide to creating a custom voice model from raw audio to trained StyleTTS2 model.

---

## 📊 Workflow Overview

```
1. Source Audio (YouTube, podcasts, recordings)
   ↓
2. Stem Separation (isolate clean vocals)
   ↓
3. Import & Segment (prepare audio chunks)
   ↓
4. Transcribe (auto-generate text)
   ↓
5. Export Dataset (create training files)
   ↓
6. Fine-tune Model (train custom voice)
   ↓
7. Use Custom Voice (generate speech)
```

**Estimated Time:** 2-4 hours for 1 hour of audio (plus training time)

---

## 🎵 Step 1: Obtain Source Audio

### Recommended Sources
- **YouTube videos** (interviews, podcasts, talks)
- **Audiobooks** (if you have rights)
- **Original recordings** (best quality control)
- **Public domain content**

### Quality Guidelines
✅ **Good Sources:**
- Clear speech, minimal background noise
- Consistent speaking style
- Single speaker (or isolatable)
- Professional recordings
- 128kbps+ bitrate

❌ **Avoid:**
- Heavy music/sound effects throughout
- Multiple overlapping speakers
- Poor audio quality (muffled, distorted)
- Highly compressed (low bitrate <64kbps)
- Lots of silence/dead air

### Download Audio

**From YouTube (with yt-dlp):**
```powershell
# Install yt-dlp
pip install yt-dlp

# Download audio only
yt-dlp -x --audio-format mp3 --audio-quality 0 "https://youtube.com/watch?v=VIDEO_ID"
```

**From Video Files:**
```powershell
# Extract audio with FFmpeg
ffmpeg -i video.mp4 -vn -acodec libmp3lame -q:a 2 audio.mp3
```

---

## 🎤 Step 2: Isolate Vocals with Stem Separation

This is the **most important step** for quality! Background music/noise will degrade your model.

### Launch Stem Separation UI
```powershell
cd stem-separation
.\launch_stem_separation.bat
```

Browser opens to `http://127.0.0.1:7861`

### For Single Files

**Go to:** "🔥 Demucs (Best Quality)" tab

1. **Upload Audio**: Click to upload your audio file
2. **Select Model**: Choose `htdemucs_ft` (best quality)
3. **Select Quality**: Choose `Maximum (Slow)` ⭐
4. **Output Format**: Choose `wav` (best for training)
5. **Click**: "🎬 Separate Stems"

⏱️ **Processing time:** ~2-3 minutes per minute of audio

**Result:** You'll get 4 stems:
- 🎤 **Vocals** ← This is what you need!
- 🥁 Drums
- 🎸 Bass
- 🎹 Other (instruments)

### For Batch Processing (Recommended for Multiple Files)

**Go to:** "📦 Batch Processing" tab

1. **Input Folder**: Enter path like `C:\Users\YourName\Music\Recordings`
2. **Model**: Select `htdemucs_ft`
3. **Quality**: Select `Maximum (Slow)` ⭐
4. **Format**: Select `wav`
5. **Vocals Only**: ✅ Check this (saves space)
6. **Click**: "🚀 Start Batch Processing"

⏱️ **Processing time:** ~20-30 minutes for 10 files (depends on duration)

**Output location:** `stem-outputs/batch/[your-folder-name]/htdemucs_ft/`

### Quality Verification

Listen to the vocals stem:
- ✅ Should sound clean and isolated
- ✅ Minimal bleed from instruments
- ✅ No weird artifacts or warbling
- ❌ If it sounds distorted, try `High Quality` instead of `Maximum`

---

## 📊 Step 3: Prepare Dataset with StyleTTS2

### Launch StyleTTS2 UI
```powershell
cd styletts2-setup
.\launch_styletts2.bat
```

Browser opens to `http://localhost:7860`

**Go to:** "Dataset Prep & Training" tab

### 3.1 Import Audio

**Tab:** "1️⃣ Import Audio"

1. **Speaker Name**: Enter a name (e.g., `morgan_freeman`, `david_attenborough`)
   - Use lowercase, underscores only
   - This will be your dataset identifier

2. **Upload Files**: Select all your **isolated vocal files**
   - Multiple files supported
   - Formats: MP3, WAV, FLAC, M4A, OGG

3. **Click**: "📥 Import Audio"

✅ **Result:** Files copied to `training-data/raw/[speaker_name]/`

### 3.2 Segment Audio

**Tab:** "2️⃣ Segment Audio"

1. **Select Speaker**: Choose your speaker from dropdown
2. **Chunk Duration**: 60 seconds (recommended)
   - Shorter (30s): More chunks, faster transcription
   - Longer (90s): Fewer chunks, preserves context
3. **Click**: "✂️ Segment Audio"

**What this does:**
- Converts all audio to 24kHz mono WAV (StyleTTS2 format)
- Splits long files into ~1 minute chunks
- Normalizes volume

⏱️ **Processing time:** ~1-2 minutes per hour of audio

✅ **Result:** Segmented files in `training-data/processed/[speaker_name]/`

**Check the output:**
- How many chunks created?
- Total duration?
- **Minimum:** 30 minutes
- **Good:** 1-2 hours
- **Excellent:** 4+ hours

### 3.3 Transcribe

**Tab:** "3️⃣ Transcribe"

1. **Select Speaker**: Choose your speaker
2. **Whisper Model**: Select transcription quality
   - `tiny`: Fastest, least accurate
   - `base`: ⭐ Good balance (recommended)
   - `small`: Better accuracy, slower
   - `medium`: High accuracy, much slower
   - `large`: Best accuracy, very slow

3. **Click**: "🎤 Transcribe"

**What this does:**
- Uses OpenAI Whisper to auto-generate transcripts
- GPU-accelerated (RTX 3060: ~10-30s per minute of audio)
- Saves one transcript file per audio file

⏱️ **Processing time:**
- `base`: ~10-20 seconds per minute of audio
- `small`: ~30-60 seconds per minute
- `medium`: ~2-3 minutes per minute

✅ **Result:** Transcripts in `training-data/transcripts/[speaker_name]/`

**Verify transcription quality:**
- Click "Review" to check a few samples
- Transcripts should match audio
- Minor errors are okay, major errors need manual correction

### 3.4 Export Dataset

**Tab:** "4️⃣ Export Dataset"

1. **Select Speaker**: Choose your speaker
2. **Dataset Name**: Enter a name (e.g., `morgan_freeman_dataset_v1`)
3. **Click**: "💾 Export Dataset"

**What this does:**
- Creates StyleTTS2-compatible filelist
- Format: `path/to/audio.wav|transcription text|speaker_name`
- Copies all files to organized dataset folder

✅ **Result:** Training-ready dataset in `datasets/[dataset_name]/`

**Files created:**
```
datasets/[dataset_name]/
├── train_list.txt          # Filelist for training
├── chunk_001.wav
├── chunk_002.wav
└── ... (all audio files)
```

### 3.5 Verify Dataset

**Tab:** "5️⃣ View Datasets"

1. **Select Dataset**: Choose your exported dataset
2. **Review**:
   - Total samples (audio files)
   - Total duration
   - Sample entries

**Quality check:**
- ✅ Duration: 30+ minutes minimum
- ✅ Samples: 30+ clips
- ✅ Transcripts look correct
- ✅ Audio files accessible

---

## 🎓 Step 4: Fine-Tune StyleTTS2 Model

### Prerequisites

1. **Clone StyleTTS2 Repository**
   ```powershell
   cd E:\AI
   git clone https://github.com/yl4579/StyleTTS2.git
   cd StyleTTS2
   ```

2. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Download Pre-trained Model**
   - Go to: https://huggingface.co/yl4579/StyleTTS2-LibriTTS/tree/main
   - Download all files
   - Place in: `StyleTTS2/Models/LibriTTS/`

### Copy Dataset

```powershell
# Copy your dataset to StyleTTS2 folder
cp -r E:\styletts2-dataset-toolkit\styletts2-setup\datasets\your_dataset E:\AI\StyleTTS2\Data\
```

### Configure Training

1. **Edit** `Configs/config_ft.yml`:

```yaml
# Update these settings
train_data: Data/your_dataset/train_list.txt
val_data: Data/your_dataset/train_list.txt

# GPU settings (RTX 3060 12GB)
batch_size: 4  # Reduce to 2 if OOM
max_len: 400

# Training duration
epochs: 50  # Adjust based on dataset size
save_freq: 5  # Save checkpoint every 5 epochs

# Learning rate
lr: 0.0001

# Pretrained model paths
pretrained_model: Models/LibriTTS/epoch_2nd_00100.pth
bert_path: Models/LibriTTS/bert
```

### Start Training

```powershell
python train_finetune.py --config_path ./Configs/config_ft.yml
```

⏱️ **Training time (RTX 3060):**
- 30 min dataset: ~2 hours
- 1 hour dataset: ~4 hours
- 4 hour dataset: ~12-16 hours

**Monitoring:**
- Watch console output for loss values
- Loss should gradually decrease
- Check GPU utilization: ~90-100%

**Checkpoints saved to:** `log_dir/`

### Test Checkpoints

Stop training periodically to test quality:

```powershell
# Test epoch 20
python inference.py --checkpoint log_dir/epoch_2nd_00020.pth --text "Hello, this is a test."
```

**When to stop:**
- Loss plateaus
- Test audio sounds good
- Overfitting starts (loss increases)

---

## 🎤 Step 5: Use Your Custom Voice

### Load Custom Model in Web UI

1. **Copy checkpoint** to models folder:
   ```powershell
   cp log_dir/epoch_2nd_00050.pth E:\styletts2-dataset-toolkit\styletts2-setup\models\custom\my_voice.pth
   ```

2. **Launch StyleTTS2 UI**:
   ```powershell
   cd styletts2-setup
   .\launch_styletts2.bat
   ```

3. **Load Custom Model**:
   - Go to settings (future feature)
   - Or modify `styletts2_webui.py` to load your checkpoint

### Generate Speech

1. Enter text to synthesize
2. Adjust controls:
   - **Alpha**: Voice timbre (0.5-1.0)
   - **Beta**: Prosody (0.5-1.0)
   - **Diffusion Steps**: Quality (15-20 recommended)
3. Click "Generate"

🎊 **You now have a custom voice model!**

---

## 💡 Tips & Best Practices

### Dataset Quality
- **More data = better quality**, but diminishing returns after 4 hours
- **Clean audio is critical** - stem separation quality matters most
- **Diverse speech** is better than repetitive (different sentences, emotions)
- **Manual review** recommended for final datasets

### Processing Efficiency
- Use **batch processing** for stem separation
- Test with **small subset** first (5-10 minutes) before full dataset
- **Balanced quality** for testing, **Maximum** for production
- Process overnight for large datasets

### Training Tips
- **Start with shorter training** (30 epochs) to test
- **Monitor loss curves** - should decrease steadily
- **Test early checkpoints** (epoch 15-20) before waiting for completion
- **Save multiple checkpoints** in case of overfitting

### Common Mistakes
- ❌ Skipping stem separation (background music degrades quality)
- ❌ Using low-quality source audio
- ❌ Training on too little data (<30 min)
- ❌ Not verifying transcriptions
- ❌ Overfitting (training too long on small dataset)

---

## 📈 Expected Timeline

| Task | Duration (1 hour of audio) |
|------|----------------------------|
| Download/collect audio | 15-30 min |
| Stem separation (Maximum) | 2-3 hours |
| Import & segment | 5 min |
| Transcribe (base) | 10-20 min |
| Export dataset | 2 min |
| **Total prep time** | **3-4 hours** |
| Training | 4 hours |
| **Total project time** | **7-8 hours** |

**For batch processing 10 episodes (10 hours audio):**
- Stem separation: ~20-30 hours
- Transcription: ~2-3 hours
- Training: ~40 hours
- **Total:** ~60-70 hours (mostly unattended processing)

---

## 🆘 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solutions to common issues.

**Quick fixes:**
- **OOM during training**: Reduce `batch_size` to 2
- **Poor vocal isolation**: Try `High Quality` instead of `Maximum`
- **Transcription errors**: Use `small` or `medium` Whisper model
- **Training loss not decreasing**: Check dataset quality, increase epochs

---

## 🎯 Next Steps

1. **Experiment with different speakers**
2. **Try various quality settings** to find your sweet spot
3. **Build a library of custom voices**
4. **Share your results** (with permission)

**Happy voice cloning! 🎤✨**
