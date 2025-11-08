"""
Batch Stem Separation Tool
Automatically process multiple audio files through Demucs to extract vocals
"""

import os
import sys
import torch
from pathlib import Path
import time
import argparse
from demucs.pretrained import get_model
from demucs.apply import apply_model
import demucs.separate
import torchaudio

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Batch stem separation tool for extracting vocals from audio files"
)
parser.add_argument(
    '--input',
    type=str,
    required=True,
    help='Input folder path containing audio files to process'
)
parser.add_argument(
    '--output',
    type=str,
    required=False,
    help='Output folder path (default: input_folder/vocals_only)'
)
parser.add_argument(
    '--model',
    type=str,
    default='htdemucs_ft',
    help='Demucs model name (default: htdemucs_ft)'
)
args = parser.parse_args()

# Configuration
INPUT_FOLDER = args.input
OUTPUT_FOLDER = args.output if args.output else str(Path(INPUT_FOLDER) / "vocals_only")
MODEL_NAME = args.model  # High-quality fine-tuned model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Performance optimizations
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    if hasattr(torch, 'set_float32_matmul_precision'):
        torch.set_float32_matmul_precision('high')
    torch.set_num_threads(1)
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:256'

print("="*70)
print("🎵 Batch Stem Separation - Vocal Extraction")
print("="*70)
print(f"Device: {DEVICE}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)} GB")
print(f"Model: {MODEL_NAME}")
print(f"Input: {INPUT_FOLDER}")
print(f"Output: {OUTPUT_FOLDER}")
print("="*70 + "\n")

def process_batch():
    """Process all MP3 files in the input folder"""
    
    # Create output directory
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    
    # Find all MP3 files (exclude the combined one if present)
    input_path = Path(INPUT_FOLDER)
    mp3_files = [f for f in input_path.glob("*.mp3") 
                 if "combined" not in f.name.lower()]
    
    if not mp3_files:
        print("❌ No MP3 files found!")
        return
    
    print(f"📁 Found {len(mp3_files)} MP3 files to process\n")
    
    # Load model once
    print("⏳ Loading Demucs model (this may take a minute)...")
    model = get_model(MODEL_NAME)
    model.to(DEVICE)
    model.eval()
    print("✅ Model loaded!\n")
    
    successful = 0
    failed = []
    start_time = time.time()
    
    for idx, audio_file in enumerate(mp3_files, 1):
        try:
            progress_pct = (idx-1) / len(mp3_files) * 100
            print(f"[{idx}/{len(mp3_files)} - {progress_pct:.0f}%] Processing: {audio_file.name}")
            file_start = time.time()
            
            # Validate file size
            file_size_mb = audio_file.stat().st_size / 1024 / 1024
            print(f"   📦 Size: {file_size_mb:.1f} MB")
            
            # Load audio
            wav, sr = torchaudio.load(str(audio_file))
            
            # Resample if needed (Demucs expects 44.1kHz)
            if sr != 44100:
                wav = torchaudio.transforms.Resample(sr, 44100)(wav)
            
            # Convert to mono if stereo (model expects specific format)
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)  # Duplicate mono to stereo
            
            # Move to device
            wav = wav.to(DEVICE)
            
            # Separate
            with torch.no_grad():
                sources = apply_model(model, wav.unsqueeze(0), device=DEVICE, split=True, overlap=0.25)[0]
            
            # Extract vocals (usually index 3 for htdemucs_ft: drums, bass, other, vocals)
            vocals = sources[3].cpu()
            
            # Save vocals
            output_file = Path(OUTPUT_FOLDER) / f"{audio_file.stem}_vocals.wav"
            torchaudio.save(str(output_file), vocals, 44100)
            
            elapsed = time.time() - file_start
            print(f"   ✅ Saved: {output_file.name} ({elapsed:.1f}s)")
            
            # Show VRAM usage
            if torch.cuda.is_available():
                vram_used = torch.cuda.memory_allocated() / 1024**3
                vram_reserved = torch.cuda.memory_reserved() / 1024**3
                print(f"   💾 VRAM: {vram_used:.2f}GB used, {vram_reserved:.2f}GB reserved")
            
            successful += 1
            print()  # Empty line for readability
            
            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}\n")
            failed.append(audio_file.name)
            continue
    
    # Summary
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print("\n" + "="*70)
    print("🎉 Batch Processing Complete!")
    print("="*70)
    print(f"✅ Successful: {successful}/{len(mp3_files)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for name in failed:
            print(f"   • {name}")
    print(f"⏱️  Total time: {minutes}m {seconds}s")
    print(f"📁 Output folder: {OUTPUT_FOLDER}")
    print("="*70)

if __name__ == "__main__":
    try:
        process_batch()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
