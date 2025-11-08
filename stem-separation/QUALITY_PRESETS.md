# 🎛️ Stem Separation Quality Presets

## Quality Settings Explained

### Fast
- **Overlap:** 0.1
- **Split:** True (chunked processing)
- **Shifts:** 0 (no augmentation)
- **Speed:** ~15-20 seconds per minute of audio
- **Best for:** Quick testing, previewing results

### Balanced (Default)
- **Overlap:** 0.25
- **Split:** True
- **Shifts:** 0
- **Speed:** ~30-40 seconds per minute of audio
- **Best for:** General purpose separation

### High Quality
- **Overlap:** 0.5
- **Split:** True
- **Shifts:** 1 (test-time augmentation)
- **Speed:** ~60-90 seconds per minute of audio
- **Best for:** High-quality vocal isolation

### Maximum (Slow) ⭐ RECOMMENDED FOR VOICE CLONING
- **Overlap:** 0.75 (maximum overlap between processing windows)
- **Split:** False (processes entire file at once)
- **Shifts:** 2 (multiple test-time augmentations)
- **Speed:** ~2-3 minutes per minute of audio
- **Best for:** Maximum quality vocal extraction for voice cloning datasets

## Parameter Details

### Overlap
Controls how much processing windows overlap. Higher values mean better continuity and fewer artifacts at boundaries.
- 0.1 = minimal overlap (fast, possible artifacts)
- 0.75 = maximum overlap (slow, cleanest results)

### Split
- **True:** Processes audio in chunks (memory efficient, slight quality trade-off)
- **False:** Processes entire file at once (uses more VRAM, best quality)

### Shifts
Test-time augmentation that processes the audio multiple times with random shifts and averages results.
- 0 = no augmentation (fast)
- 1 = one augmentation pass (~2x slower, better)
- 2 = two augmentation passes (~3x slower, best quality)

## Recommendations by Use Case

### Voice Cloning Dataset Preparation
**Use:** Maximum (Slow)
- Clean vocals are critical for training quality
- Processing time is worth the quality improvement
- Reduces artifacts that could affect voice model

### Music Production
**Use:** High Quality or Maximum
- Professional results need high separation quality
- Time investment pays off in final mix

### Quick Preview/Testing
**Use:** Fast
- Check if source material is suitable
- Test different models quickly

### Batch Processing Large Libraries
**Use:** Balanced or High Quality
- Good balance for processing many files
- Maximum may be too slow for hundreds of files

## Performance Impact (RTX 3060, 3-minute song)

| Preset | Processing Time | VRAM Usage | Quality Score |
|--------|----------------|------------|---------------|
| Fast | ~45 seconds | 2-3 GB | Good |
| Balanced | ~1.5 minutes | 2-3 GB | Very Good |
| High Quality | ~3-4 minutes | 3-4 GB | Excellent |
| Maximum (Slow) | ~6-9 minutes | 4-6 GB | Outstanding |

## Tips for Best Results

1. **Start with Maximum quality** for voice cloning - the quality difference is significant
2. **Use Fast preset** to test if a song will separate well before committing to Maximum
3. **Monitor VRAM** - if you get OOM errors with Maximum, try High Quality
4. **WAV format** preserves maximum quality (no compression artifacts)
5. **Source quality matters** - clean recordings separate better than compressed/low-quality audio

## Technical Background

The quality improvements come from:
- **Higher overlap** reduces boundary artifacts where processing windows meet
- **No splitting** allows the model to see the entire context, improving coherence
- **Shifts augmentation** creates ensemble predictions that average out errors

These settings essentially trade compute time for separation quality by making the model work harder and smarter on your audio.
