# promptgen_gui/utils.py
import os

def scan_directory(startpath='.', exclude_paths=None, include_exts=None, sort_items=True):
    """
    Scans a directory recursively and returns a sorted list of items (files/dirs)
    that match the filter criteria.
    """
    items = []
    exclude_substrings = exclude_paths or []
    abs_startpath = os.path.abspath(startpath)

    for root, dirs, files in os.walk(startpath, topdown=True):
        rel_root = os.path.relpath(root, abs_startpath)
        if rel_root == '.':
            rel_root = ''

        # Filter directories in-place to prevent os.walk from traversing them
        dirs[:] = [d for d in dirs if not any(ex in os.path.join(rel_root, d).replace('\\', '/') for ex in exclude_substrings)]

        # Add directories for the current level
        for d in sorted(dirs):
            items.append((os.path.join(rel_root, d).replace('\\', '/'), 'dir'))

        # Add filtered files for the current level
        for f in sorted(files):
            rel_f_path = os.path.join(rel_root, f).replace('\\', '/')
            if any(ex in rel_f_path for ex in exclude_substrings):
                continue
            if include_exts and not any(f.lower().endswith(f".{ext.lower()}") for ext in include_exts):
                continue
            items.append((rel_f_path, 'file'))

    if sort_items:
        items.sort(key=lambda x: (x[0].count(os.sep), x[1] == 'file', x[0].lower()))
    return items

def generate_tree_structure_string(root_dir, relevant_paths, exclude_paths=None):
    """
    Generates a tree-like string for a given set of relevant paths, pruning
    any branches that do not contain a relevant file or folder.
    """
    if not relevant_paths:
        return ""

    structure = {} # A nested dict representing the file system
    for path in sorted(list(relevant_paths)):
        parts = path.split('/')
        current_level = structure
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    lines = []
    def build_lines(d, prefix=""):
        # Get sorted items, ensuring files come after directories if names are same
        items = sorted(d.keys(), key=lambda k: (not bool(d[k]), k))
        for i, name in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}{name}"
            
            # If the item is a directory (has children), add a slash
            if d[name]:
                line += "/"
            lines.append(line)
            
            # Recurse into the directory
            if d[name]:
                new_prefix = prefix + ("    " if is_last else "│   ")
                build_lines(d[name], new_prefix)

    # Start building the tree string
    lines.append(f"{os.path.basename(os.path.abspath(root_dir))}/")
    build_lines(structure)
    return "\n".join(lines)