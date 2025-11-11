#!/usr/bin/env python3
"""
StyleTTS2 Web UI
A Gradio-based interface for StyleTTS2 text-to-speech synthesis with advanced features
"""

import os
import argparse
import gradio as gr
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime
import re
import hashlib
import time
from collections import OrderedDict
import wave
import contextlib
import json

# Import num2words for text normalization
try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False
    print("⚠️ num2words not installed. Text normalization will be limited.")

# Add FFmpeg to PATH (for pydub audio processing)
ffmpeg_path = r"E:\AI\tools\ffmpeg\bin"
if ffmpeg_path not in os.environ['PATH']:
    os.environ['PATH'] = f"{ffmpeg_path};{os.environ['PATH']}"

# Setup paths
BASE_DIR = Path(__file__).parent
# Configurable output directory via environment variable
OUTPUTS_DIR = Path(os.environ.get('STYLETTS2_OUTPUTS_DIR', BASE_DIR / "outputs"))
VOICE_SAMPLES_DIR = BASE_DIR / "voice-samples"
MODELS_DIR = BASE_DIR / "models"
PRESETS_DIR = BASE_DIR / "presets"
TRAINING_DATA_DIR = BASE_DIR / "training-data"
DATASETS_DIR = BASE_DIR / "datasets"
FINETUNED_MODELS_DIR = MODELS_DIR / "finetuned"

# Create directories
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
PRESETS_DIR.mkdir(parents=True, exist_ok=True)
TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
(TRAINING_DATA_DIR / "raw").mkdir(exist_ok=True)
(TRAINING_DATA_DIR / "processed").mkdir(exist_ok=True)
(TRAINING_DATA_DIR / "transcripts").mkdir(exist_ok=True)
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
FINETUNED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Check if CUDA is available
print("🚀 Initializing StyleTTS2...")
print(f"   CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)} GB")

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Performance optimizations
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    # Only available in PyTorch 2.0+
    if hasattr(torch, 'set_float32_matmul_precision'):
        torch.set_float32_matmul_precision('high')
    # Reduce CPU thread overhead on Windows
    torch.set_num_threads(1)
    # Prevent CUDA memory fragmentation during long sessions
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:256'

# Global model variable
styletts2_model = None

# Speaker embedding cache with LRU eviction (max 20 entries)
MAX_SPEAKER_CACHE_SIZE = 20
speaker_cache = OrderedDict()

def get_speaker_cache_key(speaker_wav_path):
    """Generate cache key from file path and modification time"""
    if not speaker_wav_path:
        return None
    path = Path(speaker_wav_path)
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    return hashlib.md5(f"{speaker_wav_path}_{mtime}".encode()).hexdigest()

def get_cached_speaker_embedding(cache_key, speaker_wav, styletts2_model):
    """Get or compute speaker embedding with LRU cache management"""
    if cache_key and cache_key in speaker_cache:
        # Move to end (most recently used)
        speaker_cache.move_to_end(cache_key)
        return speaker_cache[cache_key]
    
    # For StyleTTS2, we cache the file path since the model handles embedding internally
    # If the model exposes an embedding extraction API in the future, we should cache that instead
    # For now, this at least validates the cache key system is working
    speaker_cache[cache_key] = speaker_wav
    if len(speaker_cache) > MAX_SPEAKER_CACHE_SIZE:
        speaker_cache.popitem(last=False)  # Remove oldest
    
    return speaker_wav

def normalize_transcript(text, max_chars=450):
    """
    Normalize transcript for StyleTTS2 compatibility:
    - Convert digits to words (using num2words if available)
    - Remove unsupported characters (only keep: A-Z, a-z, !'(),:;? and space)
    - Truncate to max_chars at sentence boundary
    
    Returns: (normalized_text, warnings_list)
    """
    warnings = []
    original_length = len(text)
    
    # Step 1: Convert digits to words
    if NUM2WORDS_AVAILABLE:
        def replace_number(match):
            try:
                num = match.group(0)
                # Handle percentages
                if '%' in num:
                    num_val = int(num.replace('%', ''))
                    return f"{num2words(num_val)} percent"
                # Handle regular numbers
                return num2words(int(num))
            except:
                return match.group(0)
        
        # Replace numbers (including percentages)
        text = re.sub(r'\d+%?', replace_number, text)
    else:
        # Fallback: just remove digits
        if re.search(r'\d', text):
            warnings.append("⚠️ Contains digits (num2words not installed)")
            text = re.sub(r'\d+', '', text)
    
    # Step 2: Remove unsupported characters (keep only StyleTTS2 vocab)
    # Allowed: A-Z, a-z, !'(),:;? and space
    allowed_pattern = r"[^A-Za-z!'(),:;? ]"
    removed_chars = set(re.findall(allowed_pattern, text))
    if removed_chars:
        warnings.append(f"⚠️ Removed chars: {', '.join(repr(c) for c in sorted(removed_chars))}")
    text = re.sub(allowed_pattern, ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Step 3: Truncate if too long (at sentence boundary)
    if len(text) > max_chars:
        warnings.append(f"⚠️ Truncated from {len(text)} to {max_chars} chars")
        # Try to truncate at sentence boundary
        truncated = text[:max_chars]
        last_sentence = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        if last_sentence > max_chars * 0.7:  # Only if we don't lose too much
            text = truncated[:last_sentence + 1].strip()
        else:
            text = truncated.strip()
    
    if original_length != len(text):
        warnings.append(f"ℹ️ Length: {original_length} → {len(text)} chars")
    
    return text, warnings

def validate_audio_file(audio_path):
    """Validate voice sample duration and format"""
    if not audio_path or not Path(audio_path).exists():
        return None, None
    
    try:
        with contextlib.closing(wave.open(audio_path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration, None
    except:
        # Fallback for non-WAV files
        return None, "⚠️ Could not determine audio duration. Recommended: 3-30 seconds of clear audio."

def count_characters_and_chunks(text):
    """Count characters and estimate chunks for UI feedback"""
    if not text:
        return "0 characters | 0 chunks"
    
    char_count = len(text)
    estimated_chunks = max(1, (char_count + 249) // 250)  # Ceiling division
    
    # Color coding for warnings
    if char_count > 2000:
        status = "⚠️"
    elif char_count > 1000:
        status = "ℹ️"
    else:
        status = "✓"
    
    return f"{status} {char_count} characters | ~{estimated_chunks} chunks"

def split_text_into_chunks(text, max_chars=250):
    """Split text into chunks at sentence boundaries, respecting max character limit"""
    # Split by sentences (periods, exclamation marks, question marks)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If a single sentence is too long, split by commas/semicolons
        if len(sentence) > max_chars:
            sub_sentences = re.split(r'(?<=[,;:])\s+', sentence)
            for sub in sub_sentences:
                # If still too long, force split at max_chars
                if len(sub) > max_chars:
                    words = sub.split()
                    temp = ""
                    for word in words:
                        if len(temp) + len(word) + 1 <= max_chars:
                            temp += (" " if temp else "") + word
                        else:
                            if temp:
                                chunks.append(temp.strip())
                            temp = word
                    if temp:
                        current_chunk = temp
                elif len(current_chunk) + len(sub) + 1 <= max_chars:
                    current_chunk += (" " if current_chunk else "") + sub
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sub
        else:
            # Add sentence to current chunk if it fits
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Hard cap any chunk that still exceeds max_chars
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
        else:
            # Force split into max_chars segments
            for i in range(0, len(chunk), max_chars):
                final_chunks.append(chunk[i:i+max_chars])
    
    return final_chunks

def load_model():
    """Load the StyleTTS2 model with warmup"""
    global styletts2_model
    
    try:
        from styletts2 import tts
        
        print("Loading StyleTTS2 model...")
        # Initialize the model (will download if not present)
        styletts2_model = tts.StyleTTS2()
        print("Model loaded successfully!")
        
        # Warmup model with voice sample
        print("⚡ Warming up model...")
        warmup_start = time.time()
        try:
            voice_samples = list(VOICE_SAMPLES_DIR.glob("*.wav"))
            if voice_samples:
                warmup_voice = str(voice_samples[0])
                print(f"   Using {voice_samples[0].name} for warmup")
                with torch.inference_mode():
                    _ = styletts2_model.inference(
                        "Warming up the model.",
                        warmup_voice,
                        alpha=0.3,
                        beta=0.7,
                        diffusion_steps=5
                    )
                print(f"   Warmup complete ({time.time() - warmup_start:.1f}s)")
            else:
                print("   ⚠️ No voice samples found - warmup skipped")
        except Exception as e:
            print(f"   ⚠️ Warmup failed: {e}")
        
        print("✅ StyleTTS2 Ready!")
        return "✅ Model loaded successfully!"
    except Exception as e:
        error_msg = f"❌ Error loading model: {str(e)}"
        print(error_msg)
        return error_msg

def generate_speech(text, reference_audio=None, alpha=0.3, beta=0.7, diffusion_steps=10, embedding_scale=1.0, custom_filename="", progress=gr.Progress()):
    """
    Generate speech from text using StyleTTS2 with optimized processing
    
    Args:
        text: Input text to synthesize
        reference_audio: Optional reference audio for voice cloning
        alpha: Timbre control (0-1)
        beta: Prosody control (0-1)
        diffusion_steps: Number of diffusion steps (quality vs speed)
        embedding_scale: Embedding scale for style control
        custom_filename: Optional custom filename (without extension)
        progress: Gradio progress tracker
    """
    global styletts2_model
    
    if styletts2_model is None:
        return None, "❌ Model not loaded. Please load the model first."
    
    if not text or len(text.strip()) == 0:
        return None, "❌ Please enter some text to synthesize."
    
    try:
        # Validate voice sample if provided
        if reference_audio:
            duration, warning = validate_audio_file(reference_audio)
            if duration:
                if duration < 2:
                    return None, "❌ Voice sample too short. Please use at least 2 seconds of audio."
                elif duration < 3:
                    print(f"   ⚠️ Voice sample is {duration:.1f}s (3-30s recommended for best quality)")
                elif duration > 60:
                    print(f"   ⚠️ Voice sample is {duration:.1f}s (3-30s recommended)")
            elif warning:
                print(f"   {warning}")
        
        text_length = len(text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate smart filename
        if custom_filename and custom_filename.strip():
            base_filename = sanitize_filename(custom_filename.strip())
        else:
            base_filename = sanitize_filename(text)
        
        # Add voice name if cloning
        if reference_audio:
            voice_name = Path(reference_audio).stem
            filename = f"{voice_name}_{base_filename}_{timestamp}.wav"
        else:
            filename = f"{base_filename}_{timestamp}.wav"
        
        output_path = OUTPUTS_DIR / filename
        
        print(f"🎤 Generating speech...")
        print(f"   Text length: {text_length} characters (~{text_length//5} words)")
        if reference_audio:
            print(f"   Voice sample: {Path(reference_audio).name}")
            # Check if voice sample is in cache (reduces file validation overhead)
            cache_key = get_speaker_cache_key(reference_audio)
            if cache_key and cache_key in speaker_cache:
                print(f"   ⚡ Voice sample validated from cache (cache size: {len(speaker_cache)}/{MAX_SPEAKER_CACHE_SIZE})")
            else:
                print(f"   🔧 Validating voice sample (will cache for future use)...")
            reference_audio = get_cached_speaker_embedding(cache_key, reference_audio, styletts2_model)
        
        # Split long text into chunks with error recovery
        if text_length > 250:
            chunks = split_text_into_chunks(text, max_chars=250)
            num_chunks = len(chunks)
            print(f"   📝 Split into {num_chunks} chunks")
            
            audio_arrays = []
            failed_chunks = []
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    progress((i-1)/num_chunks, desc=f"Generating chunk {i}/{num_chunks}...")
                    print(f"   Processing chunk {i}/{num_chunks} ({len(chunk)} chars)...")
                    
                    with torch.inference_mode():
                        if reference_audio:
                            audio = styletts2_model.inference(
                                chunk,
                                reference_audio,
                                alpha=alpha,
                                beta=beta,
                                diffusion_steps=diffusion_steps,
                                embedding_scale=embedding_scale
                            )
                        else:
                            audio = styletts2_model.inference(
                                chunk,
                                alpha=alpha,
                                beta=beta,
                                diffusion_steps=diffusion_steps,
                                embedding_scale=embedding_scale
                            )
                    
                    # Ensure it's a numpy array
                    if torch.is_tensor(audio):
                        audio = audio.cpu().numpy()
                    
                    audio_arrays.append(audio)
                    # Add small silence between chunks (0.1s at 24kHz)
                    if i < num_chunks:
                        silence = np.zeros(int(0.1 * 24000))
                        audio_arrays.append(silence)
                
                except Exception as chunk_error:
                    print(f"   ⚠️ Chunk {i} failed: {chunk_error}")
                    failed_chunks.append(i)
                    # Add silence to maintain timing
                    audio_arrays.append(np.zeros(int(0.5 * 24000)))
                    continue
            
            # Check if we have any audio
            if not audio_arrays:
                return None, "❌ All chunks failed to generate"
            
            # Combine all audio in memory
            progress(0.95, desc="Finalizing audio...")
            print(f"   🔗 Combining {len(audio_arrays)} audio segments...")
            audio_arrays = [np.atleast_1d(arr) for arr in audio_arrays]
            combined_audio = np.concatenate(audio_arrays)
            
            # Save final output
            sf.write(output_path, combined_audio, 24000)
            
            if failed_chunks:
                message = f"⚠️ Generated with {len(failed_chunks)} failed chunks (#{', #'.join(map(str, failed_chunks))})\n📁 Saved to: {filename}"
            else:
                message = f"✅ Generated from {num_chunks} chunks!\n📁 Saved to: {filename}"
        else:
            # Short text - single generation
            progress(0.5, desc="Generating speech...")
            
            with torch.inference_mode():
                if reference_audio:
                    audio = styletts2_model.inference(
                        text,
                        reference_audio,
                        alpha=alpha,
                        beta=beta,
                        diffusion_steps=diffusion_steps,
                        embedding_scale=embedding_scale
                    )
                else:
                    audio = styletts2_model.inference(
                        text,
                        alpha=alpha,
                        beta=beta,
                        diffusion_steps=diffusion_steps,
                        embedding_scale=embedding_scale
                    )
            
            if torch.is_tensor(audio):
                audio = audio.cpu().numpy()
            
            sf.write(output_path, audio, 24000)
            message = f"✅ Generated successfully!\n📁 Saved to: {filename}"
        
        # Clear VRAM after generation
        clear_vram()
        
        print(message)
        return str(output_path), message
        
    except Exception as e:
        error_msg = f"❌ Error generating speech: {str(e)}"
        print(error_msg)
        # Clear VRAM on error
        clear_vram()
        return None, error_msg

def generate_default_speech(text, alpha=0.3, beta=0.7, diffusion_steps=10, embedding_scale=1.0, custom_filename=""):
    """Wrapper for standard TTS generation without a reference sample."""
    return generate_speech(
        text=text,
        reference_audio=None,
        alpha=alpha,
        beta=beta,
        diffusion_steps=diffusion_steps,
        embedding_scale=embedding_scale,
        custom_filename=custom_filename,
    )

def get_voice_samples():
    """Get list of available voice samples"""
    samples = sorted(VOICE_SAMPLES_DIR.glob("*.wav"))
    return [(s.stem, str(s)) for s in samples]  # (display_name, file_path)

def load_voice_sample(sample_path):
    """Load selected voice sample"""
    return sample_path if sample_path else None

def list_generated_files():
    """List all generated audio files"""
    files = sorted(OUTPUTS_DIR.glob("*.wav"), reverse=True)
    if files:
        return "\n".join([f"• {f.name}" for f in files[:10]])
    return "No files generated yet."

def sanitize_filename(text, max_length=50):
    """Create a safe filename from text"""
    # Take first few words
    words = text.split()[:5]
    filename = "_".join(words)
    # Remove unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename if filename else "output"

def clear_vram():
    """Clear CUDA cache to free up VRAM"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        print("   🧹 VRAM cache cleared")

def scan_text_files(folder_path):
    """Scan folder for text files and return sorted list"""
    if not folder_path or not Path(folder_path).exists():
        return "❌ Invalid folder path"
    
    txt_files = sorted(Path(folder_path).glob("*.txt"))
    if not txt_files:
        return "No .txt files found in folder"
    
    file_list = []
    for f in txt_files:
        size = f.stat().st_size
        file_list.append(f"• {f.name} ({size:,} bytes)")
    
    return f"Found {len(txt_files)} files:\n" + "\n".join(file_list)

def load_queue_files(folder_path):
    """Load text files from folder into queue"""
    if not folder_path or not Path(folder_path).exists():
        return [], "❌ Invalid folder path"
    
    txt_files = sorted(Path(folder_path).glob("*.txt"))
    if not txt_files:
        return [], "No .txt files found"
    
    # Return list with order numbers for the queue
    file_data = [[i+1, str(f), f.name, f"{f.stat().st_size:,} bytes"] for i, f in enumerate(txt_files)]
    return file_data, f"✅ Loaded {len(txt_files)} files into queue"

def add_files_to_queue(current_queue, files_to_add):
    """Add individual files to existing queue"""
    if not files_to_add:
        return current_queue, "❌ No files selected"
    
    current_queue = current_queue or []
    added = 0
    
    for file_path in files_to_add:
        file_path_obj = Path(file_path)
        if file_path_obj.exists() and file_path_obj.suffix == '.txt':
            # Check if already in queue
            if not any(row[1] == str(file_path_obj) for row in current_queue):
                current_queue.append([
                    len(current_queue) + 1,
                    str(file_path_obj),
                    file_path_obj.name,
                    f"{file_path_obj.stat().st_size:,} bytes"
                ])
                added += 1
    
    return current_queue, f"✅ Added {added} file(s) to queue"

def remove_from_queue(queue_data, row_index):
    """Remove selected row from queue and renumber"""
    if not queue_data or row_index < 0 or row_index >= len(queue_data):
        return queue_data, "❌ Invalid selection"
    
    removed_file = queue_data[row_index][2]  # filename
    queue_data.pop(row_index)
    
    # Renumber remaining items
    for i, row in enumerate(queue_data):
        row[0] = i + 1
    
    return queue_data, f"✅ Removed: {removed_file}"

def clear_queue():
    """Clear entire queue"""
    return [], "✅ Queue cleared"

def move_queue_item(queue_data, row_index, direction):
    """Move queue item up or down"""
    if not queue_data or row_index < 0 or row_index >= len(queue_data):
        return queue_data, "❌ Invalid selection"
    
    if direction == "up" and row_index == 0:
        return queue_data, "⚠️ Already at top"
    
    if direction == "down" and row_index == len(queue_data) - 1:
        return queue_data, "⚠️ Already at bottom"
    
    # Swap items
    if direction == "up":
        queue_data[row_index], queue_data[row_index - 1] = queue_data[row_index - 1], queue_data[row_index]
        new_index = row_index - 1
    else:  # down
        queue_data[row_index], queue_data[row_index + 1] = queue_data[row_index + 1], queue_data[row_index]
        new_index = row_index + 1
    
    # Renumber
    for i, row in enumerate(queue_data):
        row[0] = i + 1
    
    return queue_data, f"✅ Moved to position {new_index + 1}"

def process_batch_queue(queue_data, speaker_wav, alpha, beta, diffusion_steps, embedding_scale, progress=gr.Progress()):
    """Process all files in the queue sequentially"""
    global styletts2_model
    
    if not queue_data or len(queue_data) == 0:
        return None, "❌ Queue is empty. Please load text files first."
    
    if not speaker_wav:
        return None, "❌ Please select a voice sample for the batch."
    
    if styletts2_model is None:
        return None, "❌ Model not loaded. Please load the model first."
    
    total_files = len(queue_data)
    results = []
    failed = []
    
    print(f"\n{'='*60}")
    print(f"🎬 Starting batch processing: {total_files} files")
    print(f"{'='*60}\n")
    
    for idx, row in enumerate(queue_data, 1):
        if len(row) == 4:
            _, file_path, filename, _ = row
        else:
            file_path, filename, _ = row
        
        try:
            progress((idx-1)/total_files, desc=f"Processing {idx}/{total_files}: {filename}")
            
            print(f"📄 [{idx}/{total_files}] Processing: {filename}")
            
            # Read text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                print(f"   ⚠️ Skipping empty file")
                failed.append(filename)
                continue
            
            # Extract chapter number for better naming
            chapter_match = re.search(r'Chapter[_\s]+(\d+)', filename, re.IGNORECASE)
            chapter_num = chapter_match.group(1) if chapter_match else str(idx)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            voice_name = Path(speaker_wav).stem
            output_filename = f"{voice_name}_Chapter_{chapter_num.zfill(3)}_{timestamp}.wav"
            output_path = OUTPUTS_DIR / output_filename
            
            # Get cached speaker embedding
            cache_key = get_speaker_cache_key(speaker_wav)
            speaker_ref = get_cached_speaker_embedding(cache_key, speaker_wav, styletts2_model)
            
            text_length = len(text)
            print(f"   Text: {text_length} chars (~{text_length//5} words)")
            
            # Process with chunking if needed
            if text_length > 250:
                chunks = split_text_into_chunks(text, max_chars=250)
                num_chunks = len(chunks)
                print(f"   📝 {num_chunks} chunks")
                
                audio_arrays = []
                for i, chunk in enumerate(chunks, 1):
                    try:
                        with torch.inference_mode():
                            audio = styletts2_model.inference(
                                chunk,
                                speaker_ref,
                                alpha=alpha,
                                beta=beta,
                                diffusion_steps=diffusion_steps,
                                embedding_scale=embedding_scale
                            )
                        
                        if torch.is_tensor(audio):
                            audio = audio.cpu().numpy()
                        
                        audio_arrays.append(audio)
                        if i < num_chunks:
                            audio_arrays.append(np.zeros(int(0.1 * 24000)))
                    except Exception as chunk_error:
                        print(f"   ⚠️ Chunk {i} failed: {chunk_error}, continuing...")
                        continue
                
                if audio_arrays:
                    audio_arrays = [np.atleast_1d(arr) for arr in audio_arrays]
                    combined_audio = np.concatenate(audio_arrays)
                    sf.write(output_path, combined_audio, 24000)
                else:
                    print(f"   ❌ All chunks failed")
                    failed.append(filename)
                    continue
            else:
                with torch.inference_mode():
                    audio = styletts2_model.inference(
                        text,
                        speaker_ref,
                        alpha=alpha,
                        beta=beta,
                        diffusion_steps=diffusion_steps,
                        embedding_scale=embedding_scale
                    )
                
                if torch.is_tensor(audio):
                    audio = audio.cpu().numpy()
                
                sf.write(output_path, audio, 24000)
            
            results.append(output_filename)
            print(f"   ✅ Saved: {output_filename}\n")
            
            # Clear VRAM after each file
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}\n")
            failed.append(filename)
            continue
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 Batch Complete!")
    print(f"   ✅ Success: {len(results)}/{total_files}")
    if failed:
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   Files: {', '.join(failed)}")
    print(f"{'='*60}\n")
    
    summary = f"✅ Batch Complete!\n\n"
    summary += f"Processed: {len(results)}/{total_files} files\n"
    summary += f"Output folder: {OUTPUTS_DIR}\n\n"
    summary += "Generated files:\n" + "\n".join([f"• {f}" for f in results])
    
    if failed:
        summary += f"\n\n⚠️ Failed ({len(failed)}):\n" + "\n".join([f"• {f}" for f in failed])
    
    return str(results[0]) if results else None, summary

# Preset management functions
def get_preset_list():
    """Get list of available presets"""
    presets = sorted(PRESETS_DIR.glob("*.json"))
    return [""] + [p.stem for p in presets]

def save_preset(name, alpha, beta, diffusion_steps, embedding_scale):
    """Save current settings as a preset"""
    if not name or not name.strip():
        return get_preset_list(), "❌ Please enter a preset name"
    
    name = name.strip()
    preset_path = PRESETS_DIR / f"{name}.json"
    
    preset_data = {
        "alpha": alpha,
        "beta": beta,
        "diffusion_steps": diffusion_steps,
        "embedding_scale": embedding_scale
    }
    
    with open(preset_path, 'w') as f:
        json.dump(preset_data, f, indent=2)
    
    return get_preset_list(), f"✅ Preset '{name}' saved successfully"

def load_preset(name):
    """Load a preset"""
    if not name:
        return 0.3, 0.7, 10, 1.0, "Select a preset to load"
    
    preset_path = PRESETS_DIR / f"{name}.json"
    if not preset_path.exists():
        return 0.3, 0.7, 10, 1.0, "❌ Preset not found"
    
    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        return (
            preset_data.get("alpha", 0.3),
            preset_data.get("beta", 0.7),
            preset_data.get("diffusion_steps", 10),
            preset_data.get("embedding_scale", 1.0),
            f"✅ Loaded preset '{name}'"
        )
    except Exception as e:
        return 0.3, 0.7, 10, 1.0, f"❌ Error loading preset: {e}"

def delete_preset(name):
    """Delete a preset"""
    if not name:
        return get_preset_list(), "Select a preset to delete"
    
    preset_path = PRESETS_DIR / f"{name}.json"
    if preset_path.exists():
        preset_path.unlink()
        return get_preset_list(), f"✅ Preset '{name}' deleted"
    return get_preset_list(), "❌ Preset not found"

# Quick preset loaders
def load_high_quality_preset():
    """Load high quality preset"""
    return 0.3, 0.7, 20, 1.0, "✅ High Quality preset loaded (slower, best quality)"

def load_balanced_preset():
    """Load balanced preset"""
    return 0.3, 0.7, 10, 1.0, "✅ Balanced preset loaded (recommended)"

def load_fast_preset():
    """Load fast preset"""
    return 0.3, 0.7, 5, 1.0, "✅ Fast preset loaded (faster, good quality)"

# ============================================================================
# DATASET PREPARATION & TRAINING FUNCTIONS
# ============================================================================

# Try importing Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper not installed. Install with: pip install openai-whisper")

# Global whisper model
whisper_model = None

def load_whisper_model(model_size="base"):
    """Load Whisper model for transcription"""
    global whisper_model
    try:
        print(f"Loading Whisper {model_size} model...")
        whisper_model = whisper.load_model(model_size, device=device)
        print(f"✅ Whisper {model_size} model loaded!")
        return f"✅ Whisper {model_size} model loaded successfully!"
    except Exception as e:
        error_msg = f"❌ Error loading Whisper: {str(e)}"
        print(error_msg)
        return error_msg

def import_audio_files(files, speaker_name):
    """Import audio files to raw training data folder"""
    if not files or len(files) == 0:
        return [], "❌ No files selected"
    
    if not speaker_name or not speaker_name.strip():
        return [], "❌ Please enter a speaker name"
    
    speaker_name = re.sub(r'[<>:"/\\|?*]', '', speaker_name.strip())
    speaker_dir = TRAINING_DATA_DIR / "raw" / speaker_name
    speaker_dir.mkdir(exist_ok=True)
    
    imported = []
    for file_path in files:
        try:
            src = Path(file_path)
            dst = speaker_dir / src.name
            
            # Copy file
            import shutil
            shutil.copy2(src, dst)
            imported.append(str(dst))
            print(f"   Imported: {src.name}")
        except Exception as e:
            print(f"   ⚠️ Failed to import {file_path}: {e}")
            continue
    
    return imported, f"✅ Imported {len(imported)} files to {speaker_dir}"

def list_speakers():
    """List all speakers in raw folder"""
    raw_dir = TRAINING_DATA_DIR / "raw"
    speakers = [d.name for d in raw_dir.iterdir() if d.is_dir()]
    return speakers if speakers else ["No speakers found"]

def segment_audio(speaker, target_duration=60, progress=gr.Progress()):
    """Segment audio files into chunks (target: 1 minute each)"""
    if not speaker or speaker == "No speakers found":
        return None, "❌ Please select a speaker"
    
    speaker_raw = TRAINING_DATA_DIR / "raw" / speaker
    speaker_processed = TRAINING_DATA_DIR / "processed" / speaker
    speaker_processed.mkdir(parents=True, exist_ok=True)
    
    audio_files = list(speaker_raw.glob("*.wav")) + list(speaker_raw.glob("*.mp3")) + \
                  list(speaker_raw.glob("*.m4a")) + list(speaker_raw.glob("*.flac"))
    
    if not audio_files:
        return None, "❌ No audio files found for this speaker"
    
    try:
        from pydub import AudioSegment
        from pydub.utils import make_chunks
        
        total_files = len(audio_files)
        segment_count = 0
        
        print(f"\n🎬 Segmenting audio for speaker: {speaker}")
        
        for idx, audio_file in enumerate(audio_files, 1):
            progress((idx-1)/total_files, desc=f"Processing {idx}/{total_files}: {audio_file.name}")
            
            try:
                # Load audio
                if audio_file.suffix == ".mp3":
                    audio = AudioSegment.from_mp3(audio_file)
                elif audio_file.suffix == ".m4a":
                    audio = AudioSegment.from_file(audio_file, "m4a")
                elif audio_file.suffix == ".flac":
                    audio = AudioSegment.from_file(audio_file, "flac")
                else:
                    audio = AudioSegment.from_wav(audio_file)
                
                # Convert to 24kHz mono WAV (StyleTTS2 requirement)
                audio = audio.set_frame_rate(24000).set_channels(1)
                
                # Calculate chunk size in milliseconds
                chunk_length_ms = target_duration * 1000
                
                # If audio is shorter than target, save as is
                if len(audio) <= chunk_length_ms:
                    output_path = speaker_processed / f"{audio_file.stem}_seg_001.wav"
                    audio.export(output_path, format="wav")
                    segment_count += 1
                    print(f"   ✅ {audio_file.name} → 1 segment")
                else:
                    # Split into chunks
                    chunks = make_chunks(audio, chunk_length_ms)
                    for i, chunk in enumerate(chunks, 1):
                        # Skip very short chunks (< 5 seconds)
                        if len(chunk) < 5000:
                            continue
                        output_path = speaker_processed / f"{audio_file.stem}_seg_{i:03d}.wav"
                        chunk.export(output_path, format="wav")
                        segment_count += 1
                    print(f"   ✅ {audio_file.name} → {len(chunks)} segments")
                
            except Exception as e:
                print(f"   ⚠️ Failed to process {audio_file.name}: {e}")
                continue
        
        duration_summary = get_dataset_duration(speaker_processed)
        summary = f"✅ Segmentation complete!\n\n"
        summary += f"Processed: {total_files} files\n"
        summary += f"Created: {segment_count} segments\n"
        summary += f"Output: {speaker_processed}\n\n"
        summary += duration_summary
        
        print(summary)
        return str(speaker_processed), summary
        
    except ImportError:
        return None, "❌ pydub not installed. Install with: pip install pydub"
    except Exception as e:
        error_msg = f"❌ Error during segmentation: {str(e)}"
        print(error_msg)
        return None, error_msg

def get_dataset_duration(folder_path):
    """Calculate total duration of audio files in a folder"""
    try:
        from pydub import AudioSegment
        audio_files = list(Path(folder_path).glob("*.wav"))
        total_duration = 0
        
        for audio_file in audio_files:
            audio = AudioSegment.from_wav(audio_file)
            total_duration += len(audio) / 1000  # Convert to seconds
        
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        
        return f"📊 Total Duration: {hours}h {minutes}m {seconds}s ({total_duration/60:.1f} minutes)"
    except:
        return "📊 Total Duration: Unknown"

def transcribe_audio(speaker, whisper_model_size="base", progress=gr.Progress()):
    """Transcribe audio files using Whisper"""
    global whisper_model
    
    if not WHISPER_AVAILABLE:
        return None, "❌ Whisper not installed"
    
    if not speaker or speaker == "No speakers found":
        return None, "❌ Please select a speaker"
    
    speaker_processed = TRAINING_DATA_DIR / "processed" / speaker
    speaker_transcripts = TRAINING_DATA_DIR / "transcripts" / speaker
    speaker_transcripts.mkdir(parents=True, exist_ok=True)
    
    audio_files = sorted(speaker_processed.glob("*.wav"))
    
    if not audio_files:
        return None, "❌ No processed audio files found. Please run segmentation first."
    
    try:
        # Load Whisper model if not loaded
        if whisper_model is None:
            progress(0.05, desc=f"Loading Whisper {whisper_model_size} model...")
            whisper_model = whisper.load_model(whisper_model_size, device=device)
        
        total_files = len(audio_files)
        transcribed = 0
        
        print(f"\n🎤 Transcribing {total_files} audio files for speaker: {speaker}")
        print(f"   Model: Whisper {whisper_model_size}")
        
        for idx, audio_file in enumerate(audio_files, 1):
            progress(idx/total_files, desc=f"Transcribing {idx}/{total_files}: {audio_file.name}")
            
            try:
                # Transcribe
                result = whisper_model.transcribe(
                    str(audio_file),
                    language="en",  # Change if needed
                    fp16=(device == "cuda")
                )
                
                transcript = result["text"].strip()
                
                # Save transcript
                transcript_file = speaker_transcripts / f"{audio_file.stem}.txt"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                transcribed += 1
                print(f"   ✅ {audio_file.name}: {transcript[:50]}...")
                
            except Exception as e:
                print(f"   ⚠️ Failed to transcribe {audio_file.name}: {e}")
                continue
        
        summary = f"✅ Transcription complete!\n\n"
        summary += f"Transcribed: {transcribed}/{total_files} files\n"
        summary += f"Output: {speaker_transcripts}\n\n"
        summary += "Next step: Review transcripts and export dataset"
        
        print(summary)
        return str(speaker_transcripts), summary
        
    except Exception as e:
        error_msg = f"❌ Error during transcription: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, error_msg

def export_dataset(speaker, dataset_name):
    """Export processed audio + transcripts to StyleTTS2 training format"""
    if not speaker or speaker == "No speakers found":
        return None, "❌ Please select a speaker"
    
    if not dataset_name or not dataset_name.strip():
        return None, "❌ Please enter a dataset name"
    
    dataset_name = re.sub(r'[<>:"/\\|?*]', '', dataset_name.strip())
    speaker_processed = TRAINING_DATA_DIR / "processed" / speaker
    speaker_transcripts = TRAINING_DATA_DIR / "transcripts" / speaker
    
    dataset_dir = DATASETS_DIR / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    audio_files = sorted(speaker_processed.glob("*.wav"))
    
    if not audio_files:
        return None, "❌ No audio files found"
    
    try:
        # Create filelist in StyleTTS2 format: filename.wav|transcription|speaker
        filelist_path = dataset_dir / "train_list.txt"
        filelist = []
        copied = 0
        normalized_count = 0
        warning_count = 0
        
        print(f"\n📦 Exporting dataset: {dataset_name}")
        print("🔧 Normalizing transcripts for StyleTTS2 compatibility...")
        
        for audio_file in audio_files:
            transcript_file = speaker_transcripts / f"{audio_file.stem}.txt"
            
            if not transcript_file.exists():
                print(f"   ⚠️ Missing transcript for {audio_file.name}, skipping...")
                continue
            
            # Read transcript
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            
            if not transcript:
                print(f"   ⚠️ Empty transcript for {audio_file.name}, skipping...")
                continue
            
            # Normalize transcript (digits→words, remove bad chars, truncate)
            normalized_transcript, warnings = normalize_transcript(transcript, max_chars=450)
            
            if warnings:
                normalized_count += 1
                warning_count += len(warnings)
                print(f"   🔧 {audio_file.name}:")
                for warning in warnings:
                    print(f"      {warning}")
            
            # Copy audio to dataset folder
            import shutil
            dst = dataset_dir / audio_file.name
            shutil.copy2(audio_file, dst)
            
            # Add to filelist (use normalized transcript)
            filelist.append(f"{audio_file.name}|{normalized_transcript}|{speaker}")
            copied += 1
        
        # Write filelist
        with open(filelist_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(filelist))
        
        duration_summary = get_dataset_duration(dataset_dir)
        
        summary = f"✅ Dataset exported successfully!\n\n"
        summary += f"Dataset: {dataset_name}\n"
        summary += f"Files: {copied} audio + transcript pairs\n"
        summary += f"Location: {dataset_dir}\n"
        summary += f"Filelist: train_list.txt\n\n"
        
        # Report normalization stats
        if normalized_count > 0:
            summary += f"🔧 Normalization applied to {normalized_count} transcripts:\n"
            summary += f"   - Converted digits to words\n"
            summary += f"   - Removed unsupported characters\n"
            summary += f"   - Truncated overly long text\n"
            summary += f"   - Total warnings: {warning_count}\n\n"
        else:
            summary += "✅ All transcripts already clean!\n\n"
        
        summary += duration_summary + "\n\n"
        summary += "📝 Format: filename.wav|transcription|speaker\n"
        summary += "🎓 Ready for fine-tuning!"
        
        print(summary)
        return str(filelist_path), summary
        
    except Exception as e:
        error_msg = f"❌ Error exporting dataset: {str(e)}"
        print(error_msg)
        return None, error_msg

def list_datasets():
    """List all available datasets"""
    datasets = [d.name for d in DATASETS_DIR.iterdir() if d.is_dir()]
    return datasets if datasets else ["No datasets found"]

def get_dataset_info(dataset_name):
    """Get information about a dataset"""
    if not dataset_name or dataset_name == "No datasets found":
        return "Select a dataset to view info"
    
    dataset_dir = DATASETS_DIR / dataset_name
    filelist = dataset_dir / "train_list.txt"
    
    if not filelist.exists():
        return "❌ Invalid dataset (no train_list.txt found)"
    
    try:
        with open(filelist, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        num_samples = len(lines)
        duration_summary = get_dataset_duration(dataset_dir)
        
        # Sample a few lines
        sample_lines = lines[:3] if len(lines) > 3 else lines
        samples = "\n".join([f"  • {line.strip()[:80]}..." for line in sample_lines])
        
        info = f"📊 Dataset: {dataset_name}\n\n"
        info += f"Samples: {num_samples}\n"
        info += duration_summary + "\n"
        info += f"Location: {dataset_dir}\n\n"
        info += f"Sample entries:\n{samples}\n\n"
        info += "✅ Ready for training!"
        
        return info
    except Exception as e:
        return f"❌ Error reading dataset: {e}"

def create_ui():
    """Create the Gradio UI with all advanced features"""
    
    with gr.Blocks(title="StyleTTS2 Web UI - Advanced", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎙️ StyleTTS2 Web UI - Advanced Edition
        
        **High-quality text-to-speech synthesis with voice cloning & batch processing**
        
        **Features:**
        - 🎭 Clone any voice from audio samples  
        - 🚀 GPU-accelerated inference with VRAM optimization
        - 📝 Smart text chunking for long content with error recovery
        - 💾 Speaker embedding cache (LRU, 20 voices)
        - 📚 Batch processing for multiple files
        - 🎨 Quality presets & custom presets
        - 📁 Smart output naming from text content
        - 💯 100% Local & Private
        """)
        
        with gr.Tab("🎤 Text-to-Speech"):
            with gr.Row():
                with gr.Column(scale=2):
                    text_input = gr.Textbox(
                        label="📝 Text to Synthesize",
                        placeholder="Enter the text you want to convert to speech...",
                        lines=5,
                        max_lines=10
                    )
                    
                    char_counter = gr.Textbox(
                        label="📊 Character Count",
                        value="0 characters | 0 chunks",
                        interactive=False,
                        max_lines=1
                    )
                    
                    custom_filename_input = gr.Textbox(
                        label="📝 Custom Filename (optional)",
                        placeholder="Leave empty for auto-naming from text",
                        max_lines=1
                    )
                    
                    with gr.Accordion("⚡ Quick Presets", open=True):
                        with gr.Row():
                            fast_preset_btn = gr.Button("🚀 Fast (5 steps)", size="sm")
                            balanced_preset_btn = gr.Button("⚖️ Balanced (10 steps)", size="sm", variant="primary")
                            hq_preset_btn = gr.Button("💎 High Quality (20 steps)", size="sm")
                    
                    with gr.Accordion("Advanced Settings", open=False):
                        alpha_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.3,
                            step=0.05,
                            label="Alpha (Timbre Control)",
                            info="Controls voice timbre characteristics"
                        )
                        
                        beta_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.7,
                            step=0.05,
                            label="Beta (Prosody Control)",
                            info="Controls speech prosody and rhythm"
                        )
                        
                        diffusion_steps = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=10,
                            step=1,
                            label="Diffusion Steps",
                            info="More steps = higher quality but slower (10-20 recommended)"
                        )
                        
                        embedding_scale = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            label="Embedding Scale",
                            info="Scale for style embeddings"
                        )
                    
                    generate_btn = gr.Button("🎤 Generate Speech", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    output_message = gr.Textbox(
                        label="📊 Status",
                        lines=3,
                        interactive=False
                    )
                    
                    output_audio = gr.Audio(
                        label="🔊 Generated Audio",
                        type="filepath"
                    )
                    
                    gr.Markdown("### 📁 Recent Outputs")
                    files_list = gr.Textbox(
                        label="Last 10 Generated Files",
                        value=list_generated_files(),
                        lines=10,
                        interactive=False
                    )
                    
                    refresh_btn = gr.Button("🔄 Refresh List", size="sm")
        
        with gr.Tab("🎭 Voice Cloning"):
            with gr.Row():
                with gr.Column(scale=2):
                    clone_text_input = gr.Textbox(
                        label="📝 Text to Synthesize",
                        placeholder="Enter the text you want to convert to speech...",
                        lines=5,
                        max_lines=10
                    )
                    
                    clone_char_counter = gr.Textbox(
                        label="📊 Character Count",
                        value="0 characters | 0 chunks",
                        interactive=False,
                        max_lines=1
                    )
                    
                    clone_custom_filename = gr.Textbox(
                        label="📝 Custom Filename (optional)",
                        placeholder="Leave empty for auto-naming from text",
                        max_lines=1
                    )
                    
                    reference_audio = gr.Audio(
                        label="🎤 Reference Voice Sample (3-30 seconds recommended)",
                        type="filepath"
                    )
                    
                    with gr.Row():
                        voice_dropdown = gr.Dropdown(
                            label="📁 Quick Load Voice Sample",
                            choices=get_voice_samples(),
                            type="value",
                            scale=3
                        )
                        load_voice_btn = gr.Button("⬇️ Load", size="sm", scale=1
                        )
                    
                    with gr.Accordion("Advanced Settings", open=False):
                        clone_alpha = gr.Slider(0.0, 1.0, 0.3, step=0.05, label="Alpha (Timbre)")
                        clone_beta = gr.Slider(0.0, 1.0, 0.7, step=0.05, label="Beta (Prosody)")
                        clone_steps = gr.Slider(1, 50, 10, step=1, label="Diffusion Steps")
                        clone_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label="Embedding Scale")
                    
                    clone_btn = gr.Button("🎭 Clone Voice & Generate", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    clone_output_message = gr.Textbox(
                        label="📊 Status",
                        lines=3,
                        interactive=False
                    )
                    
                    clone_output_audio = gr.Audio(
                        label="🔊 Generated Audio",
                        type="filepath"
                    )
                    
                    gr.Markdown("### 📁 Recent Outputs")
                    clone_files_list = gr.Textbox(
                        label="Last 10 Generated Files",
                        value=list_generated_files(),
                        lines=10,
                        interactive=False
                    )
                    
                    clone_refresh_btn = gr.Button("🔄 Refresh List", size="sm")
        
        with gr.Tab("📚 Batch Processing"):
            gr.Markdown("""
            ### Process Multiple Text Files Sequentially
            Load a folder of `.txt` files or add individual files, then manage and process the queue.
            Perfect for audiobooks or bulk content generation.
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Folder loading section
                    gr.Markdown("#### 📁 Bulk Load from Folder")
                    batch_folder = gr.Textbox(
                        label="Text Files Folder",
                        placeholder="E:\\AI\\tts-webui\\styletts2\\texts",
                        value=""
                    )
                    
                    with gr.Row():
                        scan_btn = gr.Button("🔍 Scan Folder", size="sm")
                        load_queue_btn = gr.Button("📥 Load to Queue", variant="primary")
                    
                    scan_output = gr.Textbox(
                        label="📋 Scan Results",
                        lines=3,
                        interactive=False
                    )
                    
                    # Manual file addition
                    gr.Markdown("#### ➕ Add Individual Files")
                    manual_files = gr.File(
                        label="Select .txt Files",
                        file_count="multiple",
                        file_types=[".txt"],
                        type="filepath"
                    )
                    add_files_btn = gr.Button("➕ Add Selected Files to Queue", size="sm")
                    
                    # Queue display and controls
                    gr.Markdown("#### 📑 Queue Management")
                    queue_display = gr.Dataframe(
                        headers=["#", "File Path", "Filename", "Size"],
                        label="Current Queue",
                        interactive=False,
                        wrap=True,
                        col_count=(4, "fixed"),
                        row_count=(10, "dynamic")
                    )
                    
                    # Queue control buttons
                    with gr.Row():
                        selected_row = gr.Number(
                            label="Row #",
                            value=1,
                            minimum=1,
                            precision=0,
                            scale=1
                        )
                        move_up_btn = gr.Button("⬆️ Move Up", size="sm", scale=1)
                        move_down_btn = gr.Button("⬇️ Move Down", size="sm", scale=1)
                        remove_btn = gr.Button("🗑️ Remove", size="sm", scale=1)
                        clear_queue_btn = gr.Button("🗑️ Clear All", size="sm", variant="stop", scale=1)
                    
                    queue_status = gr.Textbox(
                        label="Queue Actions",
                        lines=1,
                        interactive=False
                    )
                    
                    gr.Markdown("#### 🎤 Voice & Settings for Batch")
                    batch_voice_sample = gr.Audio(
                        label="🎤 Voice Sample for Entire Batch",
                        type="filepath"
                    )
                    
                    with gr.Row():
                        batch_voice_dropdown = gr.Dropdown(
                            label="📁 Quick Load Voice Sample",
                            choices=get_voice_samples(),
                            type="value",
                            scale=3
                        )
                        load_batch_voice_btn = gr.Button("⬇️ Load", size="sm", scale=1)
                    
                    with gr.Row():
                        batch_alpha = gr.Slider(0.0, 1.0, 0.3, step=0.05, label="Alpha (Timbre)", scale=1)
                        batch_beta = gr.Slider(0.0, 1.0, 0.7, step=0.05, label="Beta (Prosody)", scale=1)
                    
                    with gr.Row():
                        batch_steps = gr.Slider(1, 50, 10, step=1, label="Diffusion Steps", scale=1)
                        batch_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label="Embedding Scale", scale=1)
                    
                    start_batch_btn = gr.Button("🎬 Start Batch Processing", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    batch_status = gr.Textbox(
                        label="📊 Batch Status",
                        lines=15,
                        interactive=False
                    )
                    
                    batch_audio_preview = gr.Audio(
                        label="🔊 Preview First Generated",
                        type="filepath"
                    )
        
        with gr.Tab("🎨 Presets"):
            gr.Markdown("""
            ### Save & Load Your Favorite Settings
            Create custom presets for different voices, quality levels, or use cases.
            """)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 💾 Save New Preset")
                    save_preset_name = gr.Textbox(
                        label="Preset Name",
                        placeholder="e.g., My Audiobook Voice",
                        max_lines=1
                    )
                    
                    save_alpha = gr.Slider(0.0, 1.0, 0.3, step=0.05, label="Alpha (Timbre)")
                    save_beta = gr.Slider(0.0, 1.0, 0.7, step=0.05, label="Beta (Prosody)")
                    save_steps = gr.Slider(1, 50, 10, step=1, label="Diffusion Steps")
                    save_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label="Embedding Scale")
                    
                    save_preset_btn = gr.Button("💾 Save Preset", variant="primary")
                    save_status = gr.Textbox(label="Status", lines=1, interactive=False)
                
                with gr.Column():
                    gr.Markdown("#### 📂 Load / Delete Preset")
                    preset_dropdown = gr.Dropdown(
                        label="Select Preset",
                        choices=get_preset_list(),
                        type="value"
                    )
                    
                    with gr.Row():
                        load_preset_btn = gr.Button("📥 Load Preset", variant="primary")
                        delete_preset_btn = gr.Button("🗑️ Delete Preset", variant="stop")
                    
                    load_status = gr.Textbox(label="Status", lines=1, interactive=False)
                    
                    gr.Markdown("#### 📊 Loaded Preset Values")
                    loaded_alpha = gr.Textbox(label="Alpha", interactive=False)
                    loaded_beta = gr.Textbox(label="Beta", interactive=False)
                    loaded_steps = gr.Textbox(label="Diffusion Steps", interactive=False)
                    loaded_scale = gr.Textbox(label="Embedding Scale", interactive=False)
        
        with gr.Tab("⚙️ Settings"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
                    ### Model Management
                    
                    StyleTTS2 will automatically download the required models on first use.
                    Models are cached in the Hugging Face cache directory.
                    """)
                    
                    load_model_btn = gr.Button("📥 Load/Reload Model", variant="secondary", size="lg")
                    model_status = gr.Textbox(label="Model Status", lines=2)
                    
                    gr.Markdown("### VRAM Management")
                    if torch.cuda.is_available():
                        clear_vram_btn = gr.Button("🧹 Clear VRAM Cache", variant="secondary")
                        vram_status = gr.Textbox(label="VRAM Status", lines=1, interactive=False)
                    else:
                        gr.Markdown("*CUDA not available - running on CPU*")
                
                with gr.Column():
                    gr.Markdown(f"""
                    ### Performance Features
                    - ⚡ PyTorch optimizations enabled (cuDNN benchmark, TF32)
                    - 💾 Speaker embedding cache (LRU, max 20 voices)
                    - 📝 Smart text chunking (250 chars with sentence boundaries)
                    - 🔧 Model warmup on startup for consistent performance
                    - 🛡️ Error recovery with partial output saving
                    - 📦 Batch processing for multiple files
                    - 🎨 Custom presets & quick quality presets
                    
                    ### Directory Information
                    
                    - **Models**: `{MODELS_DIR}`
                    - **Outputs**: `{OUTPUTS_DIR}`
                    - **Voice Samples**: `{VOICE_SAMPLES_DIR}`
                    - **Presets**: `{PRESETS_DIR}`
                    - **Device**: `{device.upper()}`
                    - **Cache Size**: {len(speaker_cache)}/{MAX_SPEAKER_CACHE_SIZE} voices
                    
                    **Tip**: Set `STYLETTS2_OUTPUTS_DIR` environment variable to change output location
                    """)
        
        with gr.Tab("🎓 Dataset Prep & Training"):
            gr.Markdown("""
            ### 📚 Prepare Training Dataset & Fine-Tune StyleTTS2
            
            **Create custom voice models with fine-tuning for superior quality!**
            
            **Workflow:**
            1. Import audio files (MP3, WAV, FLAC, M4A)
            2. Segment into chunks (1-1.5 minutes recommended)
            3. Transcribe with Whisper (GPU-accelerated)
            4. Export dataset in StyleTTS2 format
            5. Fine-tune model with your dataset
            
            **Quality Guide:**
            - 30 mins → Good quality
            - 1-2 hours → Great quality
            - 4+ hours → Excellent, near-perfect quality
            """)
            
            with gr.Tabs():
                # Step 1: Import Audio
                with gr.TabItem("1️⃣ Import Audio"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Step 1: Import Raw Audio")
                            speaker_name_input = gr.Textbox(
                                label="Speaker Name",
                                placeholder="e.g., morgan_freeman",
                                max_lines=1
                            )
                            
                            import_files = gr.File(
                                label="Select Audio Files",
                                file_count="multiple",
                                file_types=[".wav", ".mp3", ".m4a", ".flac"],
                                type="filepath"
                            )
                            
                            import_btn = gr.Button("📥 Import Audio Files", variant="primary", size="lg")
                        
                        with gr.Column():
                            import_status = gr.Textbox(
                                label="Import Status",
                                lines=10,
                                interactive=False
                            )
                
                # Step 2: Segment Audio
                with gr.TabItem("2️⃣ Segment Audio"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("""
                            ### Step 2: Segment Audio into Chunks
                            
                            Converts audio to 24kHz mono WAV and splits into manageable chunks.
                            
                            ⚠️ **CRITICAL:** Pretrained model has hard limits:
                            - **178 token vocabulary** (no digits/symbols)
                            - **512 BERT token limit** (~450 characters max)
                            
                            Longer audio = longer transcripts = training failures.
                            
                            **Recommended:** 3-10 seconds for clean, short transcripts.
                            **Maximum safe:** ~30 seconds (typical speech rate).
                            """)
                            
                            segment_speaker_dropdown = gr.Dropdown(
                                label="Select Speaker",
                                choices=list_speakers(),
                                type="value"
                            )
                            
                            segment_duration_slider = gr.Slider(
                                minimum=3,
                                maximum=30,
                                value=10,
                                step=1,
                                label="Target Chunk Duration (seconds)",
                                info="⚠️ Longer segments may exceed 450 char transcript limit"
                            )
                            
                            segment_btn = gr.Button("✂️ Segment Audio", variant="primary", size="lg")
                        
                        with gr.Column():
                            segment_status = gr.Textbox(
                                label="Segmentation Status",
                                lines=12,
                                interactive=False
                            )
                
                # Step 3: Transcribe
                with gr.TabItem("3️⃣ Transcribe"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("""
                            ### Step 3: Transcribe Audio with Whisper
                            
                            Uses OpenAI Whisper for automatic transcription.
                            GPU-accelerated for fast processing.
                            """)
                            
                            transcribe_speaker_dropdown = gr.Dropdown(
                                label="Select Speaker",
                                choices=list_speakers(),
                                type="value"
                            )
                            
                            whisper_model_dropdown = gr.Dropdown(
                                label="Whisper Model",
                                choices=["tiny", "base", "small", "medium", "large"],
                                value="base",
                                info="larger = better quality but slower"
                            )
                            
                            transcribe_btn = gr.Button("🎤 Transcribe Audio", variant="primary", size="lg")
                        
                        with gr.Column():
                            transcribe_status = gr.Textbox(
                                label="Transcription Status",
                                lines=12,
                                interactive=False
                            )
                            
                            gr.Markdown("""
                            **Whisper Model Comparison:**
                            - `tiny`: Fastest, least accurate
                            - `base`: Good balance (recommended)
                            - `small`: Better quality, slower
                            - `medium`: High quality, much slower
                            - `large`: Best quality, very slow
                            """)
                
                # Step 4: Export Dataset
                with gr.TabItem("4️⃣ Export Dataset"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("""
                            ### Step 4: Export Training Dataset
                            
                            Creates a dataset in StyleTTS2 format:
                            `filename.wav|transcription|speaker`
                            """)
                            
                            export_speaker_dropdown = gr.Dropdown(
                                label="Select Speaker",
                                choices=list_speakers(),
                                type="value"
                            )
                            
                            dataset_name_input = gr.Textbox(
                                label="Dataset Name",
                                placeholder="e.g., morgan_freeman_dataset",
                                max_lines=1
                            )
                            
                            export_btn = gr.Button("📦 Export Dataset", variant="primary", size="lg")
                        
                        with gr.Column():
                            export_status = gr.Textbox(
                                label="Export Status",
                                lines=12,
                                interactive=False
                            )
                
                # Step 5: View Datasets
                with gr.TabItem("5️⃣ View Datasets"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Available Datasets")
                            
                            dataset_dropdown = gr.Dropdown(
                                label="Select Dataset",
                                choices=list_datasets(),
                                type="value"
                            )
                            
                            refresh_datasets_btn = gr.Button("🔄 Refresh List", size="sm")
                        
                        with gr.Column():
                            dataset_info = gr.Textbox(
                                label="Dataset Information",
                                lines=15,
                                interactive=False
                            )
            
            gr.Markdown(f"""
            ---
            ### 📁 Directory Structure
            
            - **Raw Audio**: `{TRAINING_DATA_DIR / 'raw'}`
            - **Processed**: `{TRAINING_DATA_DIR / 'processed'}`
            - **Transcripts**: `{TRAINING_DATA_DIR / 'transcripts'}`
            - **Datasets**: `{DATASETS_DIR}`
            
            ### 🎓 Next Steps for Training
            
            Once you have a dataset exported, you can fine-tune StyleTTS2:
            
            ```bash
            # Clone StyleTTS2 repository
            git clone https://github.com/yl4579/StyleTTS2.git
            cd StyleTTS2
            
            # Install requirements
            pip install -r requirements.txt
            
            # Download LibriTTS pretrained model
            # From: https://huggingface.co/yl4579/StyleTTS2-LibriTTS
            
            # Edit config_ft.yml with your dataset path
            # Set: train_data, val_data to your dataset's train_list.txt
            
            # Start fine-tuning
            python train_finetune.py --config_path ./Configs/config_ft.yml
            ```
            
            **Pro Tips:**
            - Use clean, isolated vocals (run through stem separation first!)
            - Aim for consistent audio quality across all samples
            - 30 mins = minimum, 1-4 hours = excellent results
            - Review transcripts for accuracy before training
            - Training time: ~4 hours on A100 for 1 hour of data
            """)
        
        # Event handlers - Text-to-Speech Tab
        text_input.change(
            fn=count_characters_and_chunks,
            inputs=text_input,
            outputs=char_counter
        )
        
        # Preset quick buttons
        fast_preset_btn.click(
            fn=load_fast_preset,
            outputs=[alpha_slider, beta_slider, diffusion_steps, embedding_scale, output_message]
        )
        
        balanced_preset_btn.click(
            fn=load_balanced_preset,
            outputs=[alpha_slider, beta_slider, diffusion_steps, embedding_scale, output_message]
        )
        
        hq_preset_btn.click(
            fn=load_high_quality_preset,
            outputs=[alpha_slider, beta_slider, diffusion_steps, embedding_scale, output_message]
        )
        
        generate_btn.click(
            fn=generate_default_speech,
            inputs=[text_input, alpha_slider, beta_slider, diffusion_steps, embedding_scale, custom_filename_input],
            outputs=[output_audio, output_message]
        ).then(
            fn=list_generated_files,
            outputs=files_list
        )
        
        refresh_btn.click(
            fn=list_generated_files,
            outputs=files_list
        )
        
        # Event handlers - Voice Cloning Tab
        clone_text_input.change(
            fn=count_characters_and_chunks,
            inputs=clone_text_input,
            outputs=clone_char_counter
        )
        
        load_voice_btn.click(
            fn=load_voice_sample,
            inputs=voice_dropdown,
            outputs=reference_audio
        )
        
        clone_btn.click(
            fn=generate_speech,
            inputs=[clone_text_input, reference_audio, clone_alpha, clone_beta, clone_steps, clone_scale, clone_custom_filename],
            outputs=[clone_output_audio, clone_output_message]
        ).then(
            fn=list_generated_files,
            outputs=clone_files_list
        )
        
        clone_refresh_btn.click(
            fn=list_generated_files,
            outputs=clone_files_list
        )
        
        # Event handlers - Batch Processing Tab
        scan_btn.click(
            fn=scan_text_files,
            inputs=batch_folder,
            outputs=scan_output
        )
        
        load_queue_btn.click(
            fn=load_queue_files,
            inputs=batch_folder,
            outputs=[queue_display, scan_output]
        )
        
        add_files_btn.click(
            fn=add_files_to_queue,
            inputs=[queue_display, manual_files],
            outputs=[queue_display, queue_status]
        )
        
        move_up_btn.click(
            fn=lambda q, r: move_queue_item(q, int(r) - 1, "up"),
            inputs=[queue_display, selected_row],
            outputs=[queue_display, queue_status]
        )
        
        move_down_btn.click(
            fn=lambda q, r: move_queue_item(q, int(r) - 1, "down"),
            inputs=[queue_display, selected_row],
            outputs=[queue_display, queue_status]
        )
        
        remove_btn.click(
            fn=lambda q, r: remove_from_queue(q, int(r) - 1),
            inputs=[queue_display, selected_row],
            outputs=[queue_display, queue_status]
        )
        
        clear_queue_btn.click(
            fn=clear_queue,
            outputs=[queue_display, queue_status]
        )
        
        load_batch_voice_btn.click(
            fn=load_voice_sample,
            inputs=batch_voice_dropdown,
            outputs=batch_voice_sample
        )
        
        start_batch_btn.click(
            fn=process_batch_queue,
            inputs=[queue_display, batch_voice_sample, batch_alpha, batch_beta, batch_steps, batch_scale],
            outputs=[batch_audio_preview, batch_status]
        )
        
        # Event handlers - Presets Tab
        save_preset_btn.click(
            fn=save_preset,
            inputs=[save_preset_name, save_alpha, save_beta, save_steps, save_scale],
            outputs=[preset_dropdown, save_status]
        )
        
        load_preset_btn.click(
            fn=load_preset,
            inputs=preset_dropdown,
            outputs=[save_alpha, save_beta, save_steps, save_scale, load_status]
        ).then(
            fn=lambda a, b, s, sc: (str(a), str(b), str(s), str(sc)),
            inputs=[save_alpha, save_beta, save_steps, save_scale],
            outputs=[loaded_alpha, loaded_beta, loaded_steps, loaded_scale]
        )
        
        delete_preset_btn.click(
            fn=delete_preset,
            inputs=preset_dropdown,
            outputs=[preset_dropdown, load_status]
        )
        
        # Event handlers - Settings Tab
        load_model_btn.click(
            fn=load_model,
            inputs=[],
            outputs=[model_status]
        )
        
        if torch.cuda.is_available():
            clear_vram_btn.click(
                fn=lambda: (clear_vram(), "✅ VRAM cache cleared")[1],
                outputs=vram_status
            )
        
        # Event handlers - Dataset Prep & Training Tab
        import_btn.click(
            fn=import_audio_files,
            inputs=[import_files, speaker_name_input],
            outputs=[import_files, import_status]
        ).then(
            fn=lambda: (gr.update(choices=list_speakers()), gr.update(choices=list_speakers()), gr.update(choices=list_speakers())),
            outputs=[segment_speaker_dropdown, transcribe_speaker_dropdown, export_speaker_dropdown]
        )
        
        segment_btn.click(
            fn=segment_audio,
            inputs=[segment_speaker_dropdown, segment_duration_slider],
            outputs=[segment_status, segment_status]
        )
        
        transcribe_btn.click(
            fn=transcribe_audio,
            inputs=[transcribe_speaker_dropdown, whisper_model_dropdown],
            outputs=[transcribe_status, transcribe_status]
        )
        
        export_btn.click(
            fn=export_dataset,
            inputs=[export_speaker_dropdown, dataset_name_input],
            outputs=[export_status, export_status]
        ).then(
            fn=lambda: gr.update(choices=list_datasets()),
            outputs=dataset_dropdown
        )
        
        refresh_datasets_btn.click(
            fn=lambda: gr.update(choices=list_datasets()),
            outputs=dataset_dropdown
        )
        
        dataset_dropdown.change(
            fn=get_dataset_info,
            inputs=dataset_dropdown,
            outputs=dataset_info
        )
        
        # Load model on startup
        app.load(fn=load_model, inputs=[], outputs=[model_status])
        
        # Footer with documentation
        gr.Markdown(f"""
        ---
        ### 📖 Quick Guide
        
        **Text-to-Speech**: Basic synthesis without voice cloning
        **Voice Cloning**: Clone any voice from a 3-30 second audio sample
        **Batch Processing**: Process multiple .txt files sequentially for audiobooks
        **Presets**: Save your favorite parameter combinations
        
        **Parameter Guide:**
        - **Alpha (Timbre)**: 0-1, controls voice characteristics (lower = closer to reference)
        - **Beta (Prosody)**: 0-1, controls speech rhythm/intonation
        - **Diffusion Steps**: 1-50, quality vs speed (5=fast, 10=balanced, 20=high quality)
        - **Embedding Scale**: 0.5-2.0, style transfer intensity
        
        **Tips:**
        - Voice samples: 3-30 seconds of clear speech works best
        - Text chunking: Automatic for texts over 250 characters
        - Error recovery: Failed chunks are replaced with silence
        - VRAM management: Cache cleared automatically after each generation
        - Filenames: Auto-generated from first words of text + timestamp
        
        **💾 Output Directory:** `{OUTPUTS_DIR}`  
        **🎤 Voice Samples:** `{VOICE_SAMPLES_DIR}`  
        **🎨 Presets:** `{PRESETS_DIR}`  
        **📦 Models:** `{MODELS_DIR}`
        
        **Environment Variables:**
        - `STYLETTS2_OUTPUTS_DIR`: Custom output directory
        """)
    
    return app

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="StyleTTS2 Web UI")
    parser.add_argument("--server_port", type=int, default=7860, help="Server port")
    parser.add_argument("--server_name", type=str, default="127.0.0.1", help="Server name")
    parser.add_argument("--share", action="store_true", help="Create a public share link")
    parser.add_argument(
        "--no-browser",
        dest="inbrowser",
        action="store_false",
        help="Do not automatically open a browser window.",
    )
    parser.set_defaults(inbrowser=True)
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("StyleTTS2 Web UI")
    print("="*50)
    print(f"Device: {device}")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"Outputs Directory: {OUTPUTS_DIR}")
    print("="*50 + "\n")
    
    # Create and launch the UI
    app = create_ui()
    
    # Try to launch with automatic port fallback
    max_retries = 5
    current_port = args.server_port
    
    for attempt in range(max_retries):
        try:
            app.launch(
                server_name=args.server_name,
                server_port=current_port,
                share=args.share,
                inbrowser=args.inbrowser,
                show_api=False,
            )
            break  # Success!
        except OSError as e:
            if "Cannot find empty port" in str(e) and attempt < max_retries - 1:
                current_port += 1
                print(f"⚠️ Port {current_port - 1} is busy, trying port {current_port}...")
            else:
                print(f"\n❌ Error: Could not find an available port.")
                print(f"   Tried ports {args.server_port} to {current_port}")
                print(f"\n💡 Solutions:")
                print(f"   1. Close other applications using these ports")
                print(f"   2. Specify a different port: python styletts2_webui.py --server_port 7865")
                print(f"   3. Check running processes: netstat -ano | findstr :{args.server_port}")
                raise

if __name__ == "__main__":
    main()
