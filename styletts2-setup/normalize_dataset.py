"""
Dataset Normalization Script for StyleTTS2
Converts transcripts to be compatible with pretrained model:
- Converts digits to words (e.g., "19" → "nineteen")
- Removes unsupported characters (hyphens, special symbols)
- Truncates overly long transcripts at sentence boundaries
- Creates backup before modifying files
"""
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    from num2words import num2words
except ImportError:
    print("❌ Error: num2words library not found")
    print("Install with: pip install num2words")
    sys.exit(1)

# StyleTTS2 pretrained model vocabulary (178 tokens)
VOCAB_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
VOCAB_PUNCTUATION = '!\'(),.:;? '
VOCAB_ALL = VOCAB_LETTERS + VOCAB_PUNCTUATION

# BERT has 512 max tokens; approximately 450 characters is safe limit
MAX_CHARS = 450
SAFE_TRUNCATE_LIMIT = 430  # Leave margin for sentence boundary detection

def normalize_text(text):
    """Normalize text to be compatible with StyleTTS2 vocabulary."""
    
    # Convert numbers to words
    def replace_number(match):
        num_str = match.group(0)
        try:
            # Handle simple integers
            num = int(num_str)
            return num2words(num)
        except:
            return num_str
    
    text = re.sub(r'\d+', replace_number, text)
    
    # Remove or replace unsupported characters
    # Replace hyphens with spaces (common in hyphenated words)
    text = text.replace('-', ' ')
    
    # Remove any remaining unsupported characters
    cleaned = []
    for char in text:
        if char in VOCAB_ALL:
            cleaned.append(char)
    
    text = ''.join(cleaned)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def truncate_at_sentence(text, max_length=SAFE_TRUNCATE_LIMIT):
    """
    Truncate text at a sentence boundary before max_length.
    Tries to find the last complete sentence within the limit.
    """
    if len(text) <= max_length:
        return text, False
    
    # Find sentence boundaries (. ! ? followed by space or end)
    # Work backwards from max_length to find last complete sentence
    truncate_point = max_length
    
    # Look for sentence endings before the limit
    for match in re.finditer(r'[.!?]\s', text[:max_length]):
        truncate_point = match.end()
    
    if truncate_point == max_length:
        # No sentence boundary found, truncate at last space
        truncate_point = text.rfind(' ', 0, max_length)
        if truncate_point == -1:
            truncate_point = max_length
    
    truncated_text = text[:truncate_point].strip()
    was_truncated = True
    
    return truncated_text, was_truncated

def normalize_manifest(file_path, dry_run=False):
    """
    Normalize all transcripts in a manifest file.
    If dry_run=True, only show changes without modifying files.
    """
    file_path = Path(file_path)
    
    print(f"\n{'='*80}")
    print(f"{'[DRY RUN] ' if dry_run else ''}Processing: {file_path}")
    print(f"{'='*80}\n")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified_lines = []
    changes = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or '|' not in line:
            modified_lines.append(line + '\n')
            continue
        
        parts = line.split('|')
        if len(parts) < 2:
            modified_lines.append(line + '\n')
            continue
        
        wav_file = parts[0]
        original_transcript = parts[1]
        speaker_id = parts[2] if len(parts) > 2 else '0'
        
        # Normalize the transcript
        normalized = normalize_text(original_transcript)
        
        # Truncate if too long
        final_transcript, was_truncated = truncate_at_sentence(normalized, SAFE_TRUNCATE_LIMIT)
        
        # Track changes
        if final_transcript != original_transcript:
            changes.append({
                'line': i,
                'wav': wav_file,
                'original': original_transcript,
                'normalized': final_transcript,
                'truncated': was_truncated,
                'original_len': len(original_transcript),
                'final_len': len(final_transcript)
            })
        
        # Build modified line
        modified_line = f"{wav_file}|{final_transcript}|{speaker_id}\n"
        modified_lines.append(modified_line)
    
    # Report changes
    print(f"Total samples: {len(lines)}")
    print(f"Modified samples: {len(changes)}")
    
    if changes:
        print(f"\n{'='*80}")
        print("CHANGES:")
        print(f"{'='*80}\n")
        
        for change in changes:
            print(f"Line {change['line']}: {change['wav']}")
            print(f"  Original ({change['original_len']} chars): {change['original'][:80]}{'...' if len(change['original']) > 80 else ''}")
            print(f"  Modified ({change['final_len']} chars): {change['normalized'][:80]}{'...' if len(change['normalized']) > 80 else ''}")
            if change['truncated']:
                print(f"    ⚠️  TRUNCATED (removed {change['original_len'] - change['final_len']} chars)")
            print()
    
    # Save changes if not dry run
    if not dry_run and changes:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".txt.backup_{timestamp}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        print(f"✅ Backup created: {backup_path}")
        
        # Write modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        
        print(f"✅ File updated: {file_path}")
    
    return len(changes) > 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python normalize_dataset.py <manifest_file> [--apply]")
        print()
        print("Without --apply: Shows changes without modifying files (dry run)")
        print("With --apply: Creates backup and applies changes")
        print()
        print("Example:")
        print("  python normalize_dataset.py datasets/jinwoo-sung-dataset/train_list.txt")
        print("  python normalize_dataset.py datasets/jinwoo-sung-dataset/train_list.txt --apply")
        sys.exit(1)
    
    file_path = sys.argv[1]
    apply_changes = '--apply' in sys.argv
    
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    # Process file
    has_changes = normalize_manifest(file_path, dry_run=not apply_changes)
    
    if has_changes:
        if not apply_changes:
            print(f"\n{'='*80}")
            print("ℹ️  This was a dry run. No files were modified.")
            print("   To apply changes, run with --apply flag")
            print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print("✅ Changes applied successfully!")
            print("   Run validate_dataset.py to verify")
            print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("✅ No changes needed!")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
