# Examples & Screenshots

## 🖼️ Screenshots

### Stem Separation UI
![Stem Separation Main Interface](screenshots/stem-separation-main.png)
*Quality presets and single-file processing*

![Batch Processing](screenshots/batch-processing.png)
*Batch processing interface for multiple files*

### StyleTTS2 UI
![StyleTTS2 Main Interface](screenshots/styletts2-main.png)
*Text-to-speech generation interface*

![Dataset Preparation](screenshots/dataset-prep.png)
*Dataset preparation pipeline*

## 📊 Example Results

### Vocal Isolation Quality Comparison

| Quality Preset | Processing Time | Isolation Quality | Best Use Case |
|----------------|----------------|-------------------|---------------|
| Fast | 20s/min | Good | Testing/Preview |
| Balanced | 40s/min | Very Good | General Use |
| High Quality | 90s/min | Excellent | Production |
| Maximum | 2-3min/min | Outstanding | Voice Cloning ⭐ |

### Sample Audio Files

Place example audio files here to demonstrate:
- Original audio with music
- Isolated vocals (Maximum quality)
- Generated speech from trained model

```
examples/
├── audio/
│   ├── original_with_music.mp3
│   ├── isolated_vocals.wav
│   └── generated_speech.wav
└── screenshots/
    ├── stem-separation-main.png
    ├── batch-processing.png
    ├── styletts2-main.png
    └── dataset-prep.png
```

## 🎬 Sample Workflow

### 1. Input
- **Source**: 3-minute podcast clip with background music
- **Format**: MP3, 128kbps

### 2. Stem Separation
- **Model**: htdemucs_ft
- **Quality**: Maximum (Slow)
- **Time**: ~6-9 minutes
- **Result**: Clean vocal isolation

### 3. Dataset Preparation
- **Segments**: 3x 1-minute clips
- **Transcription**: Whisper (base model)
- **Time**: ~30 seconds

### 4. Training
- **Dataset Size**: 1 hour (60 clips)
- **Training Time**: ~4 hours (RTX 3060)
- **Result**: Custom voice model

## 📈 Performance Benchmarks

### Hardware: RTX 3060 12GB

| Task | Input | Time | Notes |
|------|-------|------|-------|
| Stem Separation (Maximum) | 3 min song | 6-9 min | Best quality |
| Stem Separation (Balanced) | 3 min song | 2 min | Good balance |
| Batch Processing | 10 songs (30 min) | ~1 hour | Maximum quality |
| Transcription (base) | 30 min audio | 5-10 min | GPU accelerated |
| Training | 1 hour dataset | 4 hours | 50 epochs |

## 🎯 Quality Examples

### Before Stem Separation
- Heavy background music
- Drums and bass prominent
- Vocals buried in mix

### After Maximum Quality Separation
- Clean isolated vocals
- Minimal instrumental bleed
- Minimal artifacts
- Ready for voice cloning

### Generated Speech Quality
- Natural prosody
- Consistent voice characteristics
- Minimal robotic sound
- Emotional range preserved

## 💡 Tips Demonstrated

1. **Always use Maximum quality** for voice cloning datasets
2. **Batch processing** saves time for large datasets
3. **Whisper base** model is sufficient for most transcriptions
4. **Monitor GPU** during long batch processes
5. **Test with small subset** before processing entire dataset

---

**Note**: Add your own screenshots and audio examples here to showcase your results!

Place screenshots in `examples/screenshots/` directory.
