# promptgen_gui/core.py

import os
import pyperclip
import tiktoken
from .utils import generate_tree_structure_string

try:
    encoder = tiktoken.get_encoding("cl100k_base")
    tiktoken_available = True
except (ImportError, ValueError):
    encoder = None
    tiktoken_available = False
    print("Warning: tiktoken not installed or model not found. Token counts will not be available.")
    print("To enable token counting, please run: pip install tiktoken")

# Default value, can be overridden by GUI
DEFAULT_MAX_TOKENS = 150_000

def calculate_tokens(text):
    """Calculates token count for a given text using tiktoken."""
    if not tiktoken_available or encoder is None: return 0
    return len(encoder.encode(text))

def read_file_content(filepath):
    # ... (function is unchanged) ...
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='cp1252') as f:
                return f.read()
        except Exception:
            print(f"Warning: Unable to decode file '{filepath}' with utf-8 or cp1252. Skipping content.")
            return None
    except Exception as e:
        print(f"Warning: Error reading file '{filepath}': {e}. Skipping content.")
        return None

def generate_prompt_data(root_dir, selected_paths, include_exts=None, exclude_paths=None, max_tokens=DEFAULT_MAX_TOKENS):
    if not tiktoken_available:
        return None, "Error: tiktoken library is required but not installed.\nPlease run: pip install tiktoken"

    # Stores [rel_path, size_bytes, original_tokens, current_tokens, content, status_reason]
    file_stats = []
    action_summary = []  # Stores tuples (reason, details)
    relevant_structure_paths = set()
    abs_root_dir = os.path.abspath(root_dir)

    # --- 1. Filter and Collect Stats ---
    for rel_path in selected_paths:
        abs_path = os.path.normpath(os.path.join(abs_root_dir, rel_path))
        if not os.path.isfile(abs_path): continue
        relevant_structure_paths.add(rel_path)
        temp_path = rel_path
        while parent := os.path.dirname(temp_path):
            if parent == temp_path: break
            relevant_structure_paths.add(parent)
            temp_path = parent

        content = read_file_content(abs_path)
        if content is None:
            action_summary.append(("Read Error", rel_path))
            continue
        
        tokens = calculate_tokens(content)
        file_stats.append([rel_path, os.path.getsize(abs_path), tokens, tokens, content, ""])

    if not file_stats:
        return "", "No files selected or remaining after filters."

    # --- 2. Enforce Token Limit by Truncating ---
    # Sort by token count descending to truncate largest files first.
    file_stats.sort(key=lambda x: x[2], reverse=True)
    current_total_tokens = sum(item[3] for item in file_stats)

    if current_total_tokens > max_tokens:
        overflow = current_total_tokens - max_tokens
        for i in range(len(file_stats)):
            if overflow <= 0: break
            
            rel_path, _, original_tokens, current_tokens, content, _ = file_stats[i]
            if current_tokens == 0: continue

            # Determine how many tokens to remove from this file
            tokens_to_remove = min(current_tokens, overflow)
            new_token_count = current_tokens - tokens_to_remove

            # Truncate content based on new token count
            encoded_content = encoder.encode(content)
            truncated_encoded_content = encoded_content[:new_token_count]
            new_content = encoder.decode(truncated_encoded_content)
            
            # Update the file stats in-place
            file_stats[i][3] = new_token_count # Update current_tokens
            file_stats[i][4] = new_content     # Update content
            file_stats[i][5] = "Truncated"     # Update status_reason
            
            action_summary.append(("Truncated", f"{rel_path} (from {original_tokens:,} to {new_token_count:,} tokens)"))
            overflow -= tokens_to_remove

    # --- 3. Build Clipboard Text ---
    clipboard_chunks = []
    included_files_details = []
    final_included_token_count = 0
    file_stats.sort(key=lambda x: x[0])  # Sort by path for predictable output

    for rel_path, size_bytes, _, current_tokens, content, _ in file_stats:
        clipboard_chunks.append(f"--- {rel_path} ---\n{content}")
        included_files_details.append((size_bytes, f" - {rel_path} | Size: {size_bytes:,} bytes | Tokens: {current_tokens:,}"))
        final_included_token_count += current_tokens

    # --- 4. Generate Directory Structure ---
    try:
        dir_structure_text = "Directory structure (showing relevant files/folders):\n" + \
                             generate_tree_structure_string(root_dir, relevant_structure_paths, exclude_paths=exclude_paths)
    except Exception as e:
        print(f"Error generating tree structure string: {e}")
        dir_structure_text = "Directory structure: (Error generating structure)"
    
    combined_text = dir_structure_text + "\n\n" + "\n\n".join(clipboard_chunks)

    # --- 5. Create Summary Message ---
    summary_lines = [f"Processed {len(selected_paths)} files found in selection."]
    
    action_reasons = {}
    for reason, detail in action_summary:
        action_reasons.setdefault(reason, []).append(detail)

    if action_reasons:
        summary_lines.append("\nFile Actions Taken:")
        if "Truncated" in action_reasons:
            details = action_reasons["Truncated"]
            summary_lines.append(f"  - Truncated {len(details)} file(s) to fit {max_tokens:,} token limit:")
            for detail in sorted(details):
                summary_lines.append(f"    - {detail}")
        if "Read Error" in action_reasons:
            details = action_reasons["Read Error"]
            summary_lines.append(f"  - Skipped {len(details)} file(s) due to read errors:")
            for detail in sorted(details):
                summary_lines.append(f"    - {detail}")

    summary_lines.append("\nIncluded files in clipboard (sorted by size desc):")
    if included_files_details:
        included_files_details.sort(key=lambda x: x[0], reverse=True)
        summary_lines.extend([details for _, details in included_files_details])
    else:
        summary_lines.append("   (None)")

    summary_lines.append(f"\nTotal tokens copied: {final_included_token_count:,}")
    if final_included_token_count > max_tokens: # Should not happen, but good to check
         summary_lines.append(f"WARNING: Final token count ({final_included_token_count:,}) still exceeds limit ({max_tokens:,})!")

    try:
        pyperclip.copy(combined_text)
        summary_lines.append(f"\n--- Copied to clipboard! ---")
    except Exception as e:
        error_detail = f"{e} (Is 'xclip' or 'xsel' installed on Linux?)"
        summary_lines.append(f"\n--- ERROR: Could not copy to clipboard: {error_detail} ---")

    return combined_text, "\n".join(summary_lines)