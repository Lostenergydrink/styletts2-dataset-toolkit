"""
Dataset Validation Script for StyleTTS2
Checks transcripts for compatibility issues without modifying files.
"""
import re
import sys
from pathlib import Path

# StyleTTS2 pretrained model vocabulary (178 tokens)
VOCAB_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
VOCAB_PUNCTUATION = '!\'(),.:;? '
VOCAB_ALL = VOCAB_LETTERS + VOCAB_PUNCTUATION

# BERT has 512 max tokens; approximately 450 characters is safe limit
MAX_CHARS = 450

def check_transcript(text):
    """Check a single transcript for issues. Returns list of problems."""
    issues = []
    
    # Check length
    if len(text) > MAX_CHARS:
        issues.append(f"TOO_LONG: {len(text)} chars (limit ~{MAX_CHARS})")
    
    # Check for digits
    if re.search(r'\d', text):
        digits = re.findall(r'\d+', text)
        issues.append(f"DIGITS: {', '.join(set(digits))}")
    
    # Check for unsupported characters
    unsupported = set()
    for char in text:
        if char not in VOCAB_ALL:
            unsupported.add(repr(char))
    
    if unsupported:
        issues.append(f"UNSUPPORTED_CHARS: {', '.join(sorted(unsupported))}")
    
    return issues

def validate_manifest(file_path):
    """Validate all transcripts in a manifest file."""
    print(f"\n{'='*80}")
    print(f"Validating: {file_path}")
    print(f"{'='*80}\n")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    problematic = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or '|' not in line:
            continue
        
        parts = line.split('|')
        if len(parts) < 2:
            continue
        
        wav_file = parts[0]
        transcript = parts[1]
        
        issues = check_transcript(transcript)
        if issues:
            problematic.append({
                'line': i,
                'wav': wav_file,
                'transcript': transcript,
                'issues': issues
            })
    
    # Report results
    print(f"Total samples: {total}")
    print(f"Clean samples: {total - len(problematic)}")
    print(f"Problematic samples: {len(problematic)}")
    
    if problematic:
        print(f"\n{'='*80}")
        print("ISSUES FOUND:")
        print(f"{'='*80}\n")
        
        for item in problematic:
            print(f"Line {item['line']}: {item['wav']}")
            print(f"  Transcript: {item['transcript'][:100]}{'...' if len(item['transcript']) > 100 else ''}")
            for issue in item['issues']:
                print(f"    ⚠️  {issue}")
            print()
    
    return len(problematic) == 0

def main():
    if len(sys.argv) > 1:
        # Validate specific files
        all_clean = True
        for file_path in sys.argv[1:]:
            if not validate_manifest(Path(file_path)):
                all_clean = False
    else:
        # Default: validate common manifest locations
        base_path = Path(__file__).parent
        manifests = [
            base_path / "datasets" / "jinwoo-sung-dataset" / "train_list.txt",
            base_path / "datasets" / "jinwoo-sung-dataset" / "val_list.txt",
        ]
        
        all_clean = True
        for manifest in manifests:
            if manifest.exists():
                if not validate_manifest(manifest):
                    all_clean = False
            else:
                print(f"⚠️  File not found: {manifest}")
        
    if all_clean:
        print(f"\n{'='*80}")
        print("✅ All transcripts are valid!")
        print(f"{'='*80}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*80}")
        print("❌ Validation failed. Fix issues before training.")
        print(f"{'='*80}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
