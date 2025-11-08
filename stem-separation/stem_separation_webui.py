"""
Stem Separation Web Interface
Open Source Audio Source Separation with Demucs v4 & UVR Models
Isolate vocals for voice cloning with high quality
"""

import os
import sys
import torch
import gradio as gr
from pathlib import Path
import datetime
import time
from typing import Tuple, Optional
import shutil
import subprocess

# Try importing demucs
try:
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    import demucs.separate
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
    print("⚠️ Demucs not installed. Install with: pip install demucs")

# Try importing audio-separator (UVR models)
try:
    from audio_separator.separator import Separator
    UVR_AVAILABLE = True
except ImportError:
    UVR_AVAILABLE = False
    print("⚠️ Audio Separator not installed. Install with: pip install audio-separator")

# Setup paths
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = Path(os.environ.get('STEM_OUTPUTS_DIR', BASE_DIR / 'stem-outputs'))
MODELS_DIR = BASE_DIR / "models"

# Create directories (parents=True handles nested paths)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Device selection
device = "cuda" if torch.cuda.is_available() else "cpu"

# Model caching (LOW severity fix: avoid reloading models on every request)
demucs_model_cache = {}  # {model_name: model_instance}
uvr_separator_cache = {}  # {model_name: Separator_instance}

# Quality presets for separation
QUALITY_PRESETS = {
    "Fast": {"overlap": 0.1, "split": True, "shifts": 0},
    "Balanced": {"overlap": 0.25, "split": True, "shifts": 0},
    "High Quality": {"overlap": 0.5, "split": True, "shifts": 1},
    "Maximum (Slow)": {"overlap": 0.75, "split": False, "shifts": 2},
}

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

# Check for FFmpeg
def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        subprocess.run(["ffmpeg", "-version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

FFMPEG_AVAILABLE = check_ffmpeg()

print("\n" + "="*60)
print("🎵 Stem Separation Web Interface")
print("="*60)
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)} GB")
print(f"Demucs Available: {DEMUCS_AVAILABLE}")
print(f"UVR Models Available: {UVR_AVAILABLE}")
print(f"FFmpeg Available: {FFMPEG_AVAILABLE}")
print(f"Model Caching: Enabled (faster repeat processing)")
print("="*60 + "\n")

def separate_with_demucs(
    audio_file: str,
    model_name: str = "htdemucs_ft",
    output_format: str = "wav",
    quality: str = "High Quality",
    progress=gr.Progress()
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], str]:
    """
    Separate audio using Demucs models (with model caching for speed)
    Returns paths to separated stems: vocals, drums, bass, other
    """
    if not DEMUCS_AVAILABLE:
        return None, None, None, None, "❌ Demucs is not installed. Please install it first."

    # Validate input file
    if not audio_file or not os.path.exists(audio_file):
        return None, None, None, None, "❌ Invalid audio file provided."

    # Check FFmpeg for non-WAV files
    if not FFMPEG_AVAILABLE and not audio_file.lower().endswith('.wav'):
        return None, None, None, None, "❌ FFmpeg is required for non-WAV files. Please install FFmpeg or use WAV format."

    try:
        import torchaudio
        
        # Load or retrieve cached model
        if model_name not in demucs_model_cache:
            progress(0.1, desc=f"Loading {model_name} model (first time only)...")
            print(f"\n🎵 Loading Demucs {model_name} model...")
            model = get_model(model_name)
            model.to(device)
            model.eval()
            demucs_model_cache[model_name] = model
            print(f"   ✅ Model cached for future use")
        else:
            print(f"\n🎵 Using cached Demucs {model_name} model")
            model = demucs_model_cache[model_name]
        
        print(f"   Input: {Path(audio_file).name}")
        start_time = time.time()

        progress(0.3, desc="Loading audio...")
        
        # Load audio
        wav, sr = torchaudio.load(audio_file)
        
        # Resample if needed (Demucs expects 44.1kHz)
        if sr != 44100:
            wav = torchaudio.transforms.Resample(sr, 44100)(wav)
        
        # Convert to stereo if mono
        if wav.shape[0] == 1:
            wav = wav.repeat(2, 1)
        
        # Move to device
        wav = wav.to(device)

        progress(0.5, desc="Separating audio...")
        
        # Get quality preset settings
        preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["High Quality"])
        overlap = preset["overlap"]
        split = preset["split"]
        shifts = preset["shifts"]
        
        print(f"   🎛️  Quality: {quality} (overlap={overlap}, split={split}, shifts={shifts})")
        
        # Separate with model using quality settings
        with torch.no_grad():
            sources = apply_model(model, wav.unsqueeze(0), device=device, 
                                split=split, overlap=overlap, shifts=shifts)[0]
        
        progress(0.8, desc="Saving stems...")
        
        # Create output directory
        audio_name = Path(audio_file).stem
        model_output_dir = OUTPUTS_DIR / model_name / audio_name
        model_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save stems (htdemucs order: drums, bass, other, vocals)
        stem_names = ["drums", "bass", "other", "vocals"]
        stem_paths = []
        
        for idx, stem_name in enumerate(stem_names):
            stem_audio = sources[idx].cpu()
            ext = "mp3" if output_format == "mp3" else "wav"
            stem_path = model_output_dir / f"{stem_name}.{ext}"
            
            if output_format == "mp3":
                # Save as MP3 (requires ffmpeg)
                torchaudio.save(str(stem_path), stem_audio, 44100, format="mp3", bits_per_sample=320)
            else:
                torchaudio.save(str(stem_path), stem_audio, 44100)
            
            stem_paths.append(stem_path)
        
        elapsed = time.time() - start_time
        
        drums_path, bass_path, other_path, vocals_path = stem_paths

        success_msg = f"✅ Separation complete!\n"
        success_msg += f"⏱️ Time: {elapsed:.1f}s\n"
        success_msg += f"📁 Output: {model_output_dir}\n\n"
        success_msg += "Stems generated:\n"
        success_msg += f"  • Vocals: {vocals_path.name}\n"
        success_msg += f"  • Drums: {drums_path.name}\n"
        success_msg += f"  • Bass: {bass_path.name}\n"
        success_msg += f"  • Other: {other_path.name}"

        print(success_msg)
        
        # Clear VRAM after processing
        clear_vram()

        return (
            str(vocals_path),
            str(drums_path),
            str(bass_path),
            str(other_path),
            success_msg
        )

    except ImportError:
        error_msg = "❌ torchaudio not installed. Install with: pip install torchaudio"
        print(error_msg)
        return None, None, None, None, error_msg
    except Exception as e:
        error_msg = f"❌ Error during separation: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, None, None, None, error_msg


def separate_with_uvr(
    audio_file: str,
    model_name: str = "UVR-MDX-NET-Inst_HQ_3",
    output_format: str = "wav",
    progress=gr.Progress()
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Separate audio using UVR models (with model caching for speed)
    Returns paths to primary and secondary stems
    """
    if not UVR_AVAILABLE:
        return None, None, "❌ Audio Separator is not installed. Please install it first."

    # Validate input file
    if not audio_file or not os.path.exists(audio_file):
        return None, None, "❌ Invalid audio file provided."

    # Check FFmpeg for non-WAV files
    if not FFMPEG_AVAILABLE and not audio_file.lower().endswith('.wav'):
        return None, None, "❌ FFmpeg is required for non-WAV files. Please install FFmpeg or use WAV format."

    try:
        # Load or retrieve cached separator
        cache_key = f"{model_name}_{output_format}"
        if cache_key not in uvr_separator_cache:
            progress(0.1, desc=f"Loading {model_name} model (first time only)...")
            print(f"\n🎵 Loading UVR model {model_name}...")
            
            separator = Separator(
                output_dir=str(OUTPUTS_DIR),
                output_format=output_format,
                normalization_threshold=0.9,
                output_single_stem=None,
                invert_using_spec=False,
                sample_rate=44100,
            )
            separator.load_model(model_filename=model_name)
            uvr_separator_cache[cache_key] = separator
            print(f"   ✅ Model cached for future use")
        else:
            print(f"\n🎵 Using cached UVR model {model_name}")
            separator = uvr_separator_cache[cache_key]
        
        print(f"   Input: {Path(audio_file).name}")
        start_time = time.time()

        progress(0.5, desc="Separating audio...")
        output_files = separator.separate(audio_file)

        progress(0.9, desc="Finalizing...")

        elapsed = time.time() - start_time

        success_msg = f"✅ Separation complete!\n"
        success_msg += f"⏱️ Time: {elapsed:.1f}s\n"
        success_msg += f"📁 Output folder: {OUTPUTS_DIR}\n\n"
        success_msg += "Stems generated:\n"
        for i, file in enumerate(output_files):
            success_msg += f"  • {Path(file).name}\n"

        print(success_msg)
        
        # Clear VRAM after processing
        clear_vram()

        # Return first two outputs (typically instrumental and vocals)
        primary = output_files[0] if len(output_files) > 0 else None
        secondary = output_files[1] if len(output_files) > 1 else None

        return primary, secondary, success_msg

    except Exception as e:
        error_msg = f"❌ Error during separation: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, None, error_msg


def batch_separate_demucs(
    input_folder: str,
    model_name: str = "htdemucs_ft",
    output_format: str = "wav",
    quality: str = "High Quality",
    vocals_only: bool = True,
    progress=gr.Progress()
) -> str:
    """
    Batch process all audio files in a folder
    """
    if not input_folder or not os.path.exists(input_folder):
        return "❌ Invalid input folder provided."
    
    try:
        import torchaudio
        
        # Find all audio files
        input_path = Path(input_folder)
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(input_path.glob(f"*{ext}"))
        
        if not audio_files:
            return f"❌ No audio files found in {input_folder}"
        
        # Create batch output directory
        batch_output_dir = OUTPUTS_DIR / "batch" / Path(input_folder).name / model_name
        batch_output_dir.mkdir(parents=True, exist_ok=True)
        
        result_msg = f"🎵 Batch Processing Started\n"
        result_msg += f"📁 Input: {input_folder}\n"
        result_msg += f"📂 Output: {batch_output_dir}\n"
        result_msg += f"🎛️  Quality: {quality}\n"
        result_msg += f"📦 Files: {len(audio_files)}\n\n"
        
        print("\n" + "="*70)
        print("🎵 BATCH PROCESSING STARTED")
        print("="*70)
        print(result_msg)
        
        # Load model once
        if model_name not in demucs_model_cache:
            progress(0.0, desc=f"Loading {model_name} model...")
            print(f"⏳ Loading {model_name} model...")
            model = get_model(model_name)
            model.to(device)
            model.eval()
            demucs_model_cache[model_name] = model
        else:
            model = demucs_model_cache[model_name]
        
        # Get quality settings
        preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["High Quality"])
        overlap = preset["overlap"]
        split = preset["split"]
        shifts = preset["shifts"]
        
        successful = 0
        failed = []
        start_time = time.time()
        
        for idx, audio_file in enumerate(audio_files, 1):
            try:
                progress_pct = (idx-1) / len(audio_files)
                progress(progress_pct, desc=f"Processing {idx}/{len(audio_files)}: {audio_file.name}")
                
                print(f"\n[{idx}/{len(audio_files)}] Processing: {audio_file.name}")
                file_start = time.time()
                
                # Load audio
                wav, sr = torchaudio.load(str(audio_file))
                
                # Resample if needed
                if sr != 44100:
                    wav = torchaudio.transforms.Resample(sr, 44100)(wav)
                
                # Convert to stereo if mono
                if wav.shape[0] == 1:
                    wav = wav.repeat(2, 1)
                
                wav = wav.to(device)
                
                # Separate
                with torch.no_grad():
                    sources = apply_model(model, wav.unsqueeze(0), device=device, 
                                        split=split, overlap=overlap, shifts=shifts)[0]
                
                # Save stems
                stem_names = ["drums", "bass", "other", "vocals"]
                ext = "mp3" if output_format == "mp3" else "wav"
                
                if vocals_only:
                    # Save only vocals
                    vocals = sources[3].cpu()
                    output_file = batch_output_dir / f"{audio_file.stem}_vocals.{ext}"
                    if output_format == "mp3":
                        torchaudio.save(str(output_file), vocals, 44100, format="mp3", bits_per_sample=320)
                    else:
                        torchaudio.save(str(output_file), vocals, 44100)
                    print(f"   ✅ Saved vocals: {output_file.name}")
                else:
                    # Save all stems
                    for idx_stem, stem_name in enumerate(stem_names):
                        stem_audio = sources[idx_stem].cpu()
                        output_file = batch_output_dir / f"{audio_file.stem}_{stem_name}.{ext}"
                        if output_format == "mp3":
                            torchaudio.save(str(output_file), stem_audio, 44100, format="mp3", bits_per_sample=320)
                        else:
                            torchaudio.save(str(output_file), stem_audio, 44100)
                    print(f"   ✅ Saved all stems")
                
                elapsed = time.time() - file_start
                print(f"   ⏱️  Time: {elapsed:.1f}s")
                
                successful += 1
                
                # Clear VRAM
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed.append(audio_file.name)
                continue
        
        # Summary
        total_time = time.time() - start_time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        
        result_msg += f"\n{'='*50}\n"
        result_msg += f"✅ Processing Complete!\n"
        result_msg += f"{'='*50}\n"
        result_msg += f"Successful: {successful}/{len(audio_files)}\n"
        if failed:
            result_msg += f"Failed: {len(failed)}\n"
            for name in failed[:5]:  # Show first 5 failures
                result_msg += f"  • {name}\n"
            if len(failed) > 5:
                result_msg += f"  ... and {len(failed)-5} more\n"
        result_msg += f"⏱️  Total time: {minutes}m {seconds}s\n"
        result_msg += f"📁 Output: {batch_output_dir}"
        
        print("\n" + result_msg)
        clear_vram()
        
        return result_msg
        
    except Exception as e:
        error_msg = f"❌ Batch processing error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


def clear_vram():
    """Clear CUDA cache to free up VRAM"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        print("   🧹 VRAM cache cleared")

def list_output_files():
    """List recent output files (sorted by modification time)"""
    # Collect ALL files first, then sort by mtime, then slice
    wav_files = list(OUTPUTS_DIR.rglob("*.wav"))
    mp3_files = list(OUTPUTS_DIR.rglob("*.mp3"))
    all_files = wav_files + mp3_files
    
    if not all_files:
        return "No files generated yet."
    
    # Sort by modification time (newest first), then take top 10
    files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
    return "\n".join([f"• {f.name} ({f.parent.name})" for f in files])


# Create Gradio Interface
with gr.Blocks(title="Stem Separation - Voice Isolation for Cloning", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎵 Stem Separation for Voice Cloning

    ### Isolate Vocals & Instruments with State-of-the-Art AI

    **Perfect for preparing clean vocal samples for voice cloning!**

    - 🎤 **Isolate vocals** with minimal artifacts
    - 🎸 **Separate instruments** (drums, bass, guitar, piano)
    - 🚀 **GPU-accelerated** processing
    - 💯 **100% Free & Open Source**
    """)

    with gr.Tabs():
        # Demucs Tab
        with gr.TabItem("🔥 Demucs (Best Quality)"):
            gr.Markdown("""
            ### Demucs v4 - State-of-the-Art Separation
            Hybrid Transformer model achieving 9.0 SDR. Best for high-quality vocal isolation.
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    demucs_input = gr.Audio(
                        label="🎵 Input Audio File",
                        type="filepath"
                    )

                    with gr.Row():
                        demucs_model = gr.Dropdown(
                            label="🤖 Model",
                            choices=[
                                "htdemucs_ft",  # Fine-tuned, best quality
                                "htdemucs",     # Standard, faster
                                "htdemucs_6s",  # 6 stems with guitar/piano
                                "mdx_extra",    # Alternative model
                            ],
                            value="htdemucs_ft"
                        )

                        demucs_quality = gr.Dropdown(
                            label="🎛️ Quality",
                            choices=list(QUALITY_PRESETS.keys()),
                            value="High Quality",
                            info="Higher quality = slower processing"
                        )

                        demucs_format = gr.Dropdown(
                            label="💾 Output Format",
                            choices=["wav", "mp3"],
                            value="wav"
                        )

                    demucs_btn = gr.Button("🎬 Separate Stems", variant="primary", size="lg")

                with gr.Column(scale=1):
                    demucs_status = gr.Textbox(
                        label="📊 Status",
                        lines=8,
                        interactive=False
                    )

            gr.Markdown("### 🔊 Output Stems")
            with gr.Row():
                demucs_vocals = gr.Audio(label="🎤 Vocals", type="filepath")
                demucs_drums = gr.Audio(label="🥁 Drums", type="filepath")

            with gr.Row():
                demucs_bass = gr.Audio(label="🎸 Bass", type="filepath")
                demucs_other = gr.Audio(label="🎹 Other", type="filepath")

        # Batch Processing Tab
        with gr.TabItem("📦 Batch Processing"):
            gr.Markdown("""
            ### 🚀 Batch Process Multiple Files
            Process an entire folder of audio files automatically. Perfect for processing large datasets!
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    batch_input_folder = gr.Textbox(
                        label="📁 Input Folder Path",
                        placeholder=r"C:\Users\YourName\Music\MyFolder",
                        info="Folder containing audio files to process"
                    )

                    with gr.Row():
                        batch_model = gr.Dropdown(
                            label="🤖 Model",
                            choices=[
                                "htdemucs_ft",
                                "htdemucs",
                                "htdemucs_6s",
                                "mdx_extra",
                            ],
                            value="htdemucs_ft"
                        )

                        batch_quality = gr.Dropdown(
                            label="🎛️ Quality",
                            choices=list(QUALITY_PRESETS.keys()),
                            value="Maximum (Slow)",
                            info="Recommended: Maximum for voice cloning"
                        )

                    with gr.Row():
                        batch_format = gr.Dropdown(
                            label="💾 Output Format",
                            choices=["wav", "mp3"],
                            value="wav"
                        )

                        batch_vocals_only = gr.Checkbox(
                            label="🎤 Vocals Only",
                            value=True,
                            info="Save only vocals (recommended for voice cloning)"
                        )

                    batch_btn = gr.Button("🚀 Start Batch Processing", variant="primary", size="lg")

                with gr.Column(scale=1):
                    batch_status = gr.Textbox(
                        label="📊 Status",
                        lines=20,
                        interactive=False
                    )

            gr.Markdown("""
            ### 💡 Batch Processing Tips
            - **Maximum (Slow)** quality recommended for best vocal isolation
            - Processing time: ~30-60 seconds per minute of audio (Maximum quality)
            - Check VRAM usage if processing very long files
            - Output will be saved in: `stem-outputs/batch/[folder-name]/[model]/`
            """)

        # UVR Tab
        with gr.TabItem("⚡ UVR Models (Fast)"):
            gr.Markdown("""
            ### Ultimate Vocal Remover Models
            Multiple trained models for different use cases. Faster processing.
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    uvr_input = gr.Audio(
                        label="🎵 Input Audio File",
                        type="filepath"
                    )

                    with gr.Row():
                        uvr_model = gr.Dropdown(
                            label="🤖 Model",
                            choices=[
                                "UVR-MDX-NET-Inst_HQ_3",
                                "UVR_MDXNET_KARA_2",
                                "UVR-MDX-NET-Inst_Main",
                            ],
                            value="UVR-MDX-NET-Inst_HQ_3"
                        )

                        uvr_format = gr.Dropdown(
                            label="💾 Output Format",
                            choices=["wav", "mp3"],
                            value="wav"
                        )

                    uvr_btn = gr.Button("🎬 Separate Audio", variant="primary", size="lg")

                with gr.Column(scale=1):
                    uvr_status = gr.Textbox(
                        label="📊 Status",
                        lines=8,
                        interactive=False
                    )

            gr.Markdown("### 🔊 Output Stems")
            with gr.Row():
                uvr_primary = gr.Audio(label="🎵 Primary Stem", type="filepath")
                uvr_secondary = gr.Audio(label="🎤 Secondary Stem", type="filepath")

        # Info Tab
        with gr.TabItem("ℹ️ Info & Tips"):
            gr.Markdown(f"""
            ## 💡 Tips for Best Results

            ### For Voice Cloning:
            1. **Use Demucs** (`htdemucs_ft` model) for highest quality vocal isolation
            2. **Check the vocals stem** for clean separation with minimal artifacts
            3. **Use 10-30 second clips** of isolated vocals for voice cloning
            4. **Avoid heavily processed songs** (lots of reverb, effects)

            ### Model Comparison:

            **Demucs Models:**
            - `htdemucs_ft`: Best quality, 4x slower (RECOMMENDED for voice cloning)
            - `htdemucs`: Standard quality, fast processing
            - `htdemucs_6s`: Separates guitar and piano as additional stems

            **Quality Presets:**
            - `Fast`: Quick processing, good for testing (overlap=0.1)
            - `Balanced`: Default quality-speed balance (overlap=0.25)
            - `High Quality`: Better separation, 2x slower (overlap=0.5, shifts=1)
            - `Maximum (Slow)`: Best possible quality, 3-4x slower (overlap=0.75, shifts=2) **← RECOMMENDED for voice cloning**

            **UVR Models:**
            - `UVR-MDX-NET-Inst_HQ_3`: High quality instrumental/vocal split
            - `UVR_MDXNET_KARA_2`: Optimized for karaoke (vocal removal)

            ### System Info:
            - **Device:** {device}
            {"- **GPU:** " + torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""}
            {"- **VRAM:** " + str(round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)) + " GB" if torch.cuda.is_available() else ""}
            - **Output Directory:** `{OUTPUTS_DIR}`

            ### Requirements:
            ```bash
            pip install demucs
            pip install audio-separator
            ```
            """)

            gr.Markdown("### 📁 Recent Outputs")
            files_list = gr.Textbox(
                label="Last 10 Generated Files",
                value=list_output_files(),
                lines=10,
                interactive=False
            )
            refresh_btn = gr.Button("🔄 Refresh List", size="sm")

    gr.Markdown(f"""
    ---
    **💾 Output Directory:** `{OUTPUTS_DIR}`  
    **🔗 Demucs:** [GitHub](https://github.com/facebookresearch/demucs) | **UVR:** [GitHub](https://github.com/Anjok07/ultimatevocalremovergui)

    **Perfect for creating clean vocal samples for XTTS voice cloning!**
    """)

    # Event handlers
    demucs_btn.click(
        fn=separate_with_demucs,
        inputs=[demucs_input, demucs_model, demucs_format, demucs_quality],
        outputs=[demucs_vocals, demucs_drums, demucs_bass, demucs_other, demucs_status]
    ).then(
        fn=list_output_files,
        outputs=files_list
    )

    batch_btn.click(
        fn=batch_separate_demucs,
        inputs=[batch_input_folder, batch_model, batch_format, batch_quality, batch_vocals_only],
        outputs=[batch_status]
    ).then(
        fn=list_output_files,
        outputs=files_list
    )

    uvr_btn.click(
        fn=separate_with_uvr,
        inputs=[uvr_input, uvr_model, uvr_format],
        outputs=[uvr_primary, uvr_secondary, uvr_status]
    ).then(
        fn=list_output_files,
        outputs=files_list
    )

    refresh_btn.click(
        fn=list_output_files,
        outputs=files_list
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 Starting Stem Separation Web Interface...")
    print("="*60)
    demo.queue().launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        show_error=True
    )
