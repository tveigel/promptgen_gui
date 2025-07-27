# promptgen_gui/app.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font as tkFont
import os
import threading
import sys

try:
    from ttkthemes import ThemedTk
    ttk_themes_available = True
except ImportError:
    ttk_themes_available = False

try:
    from . import core, utils
    from .core import tiktoken_available
except ImportError as e:
    messagebox.showerror("Import Error", f"Failed to import core modules: {e}\nMake sure all project files are in place.")
    sys.exit()


class PromptgenGUI:
    def __init__(self, root):
        # ... (init code is unchanged) ...
        self.root = root
        self.root.title("PromptGen GUI")
        self.root.geometry("1000x750")

        self.setup_styles_and_fonts()
        self.load_checkbox_images()

        self.current_dir = os.getcwd()

        self.checked_state = {}
        self.persistent_checked_state = {}
        self.tree_items = {}

        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.left_pane = ttk.Frame(self.paned_window, width=400)
        self.paned_window.add(self.left_pane, weight=1)
        self.right_pane = ttk.Frame(self.paned_window, width=600)
        self.paned_window.add(self.right_pane, weight=2)

        self.setup_left_pane()
        self.setup_right_pane()

        if not tiktoken_available:
            self.log_message("Warning: tiktoken not found. Token counts disabled. Run 'pip install tiktoken'.", is_error=True)
            self.copy_button.configure(state=tk.DISABLED)

        self.populate_treeview()

    # ... (setup_styles_and_fonts, load_checkbox_images are unchanged) ...
    def setup_styles_and_fonts(self):
        style = ttk.Style()
        if not ttk_themes_available or not isinstance(self.root, ThemedTk):
            try:
                style.theme_use('clam')
            except tk.TclError:
                style.theme_use('default')

        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.text_font = tkFont.nametofont("TkTextFont")
        try:
            if sys.platform == "win32":
                self.default_font.configure(family="Segoe UI", size=10)
                self.text_font.configure(family="Consolas", size=10)
            elif sys.platform == "darwin":
                self.default_font.configure(family="San Francisco", size=11)
                self.text_font.configure(family="Menlo", size=11)
            else:
                self.default_font.configure(family="DejaVu Sans", size=10)
                self.text_font.configure(family="DejaVu Sans Mono", size=10)
        except tk.TclError:
            print("Warning: Could not set preferred system fonts. Using Tk defaults.")

        style.configure('.', font=self.default_font)
        style.configure('TButton', font=self.default_font, padding=5)
        style.configure('Treeview', font=self.default_font, rowheight=int(self.default_font.metrics()['linespace'] * 1.5))
        style.configure('TLabelframe.Label', font=(self.default_font.actual('family'), self.default_font.actual('size'), 'bold'))
        style.configure("Treeview.Heading", font=(self.default_font.actual('family'), self.default_font.actual('size'), 'bold'))

    def load_checkbox_images(self):
        try:
            script_dir = os.path.dirname(__file__)
            assets_dir = os.path.join(script_dir, 'assets')
            self.img_checked = tk.PhotoImage(file=os.path.join(assets_dir, 'checked.png'))
            self.img_unchecked = tk.PhotoImage(file=os.path.join(assets_dir, 'unchecked.png'))
            print("Checkbox images loaded successfully.")
        except (FileNotFoundError, tk.TclError) as e:
            self.img_checked = None
            self.img_unchecked = None
            print(f"Warning: Could not load checkbox images: {e}. Using text fallback '[x]' / '[ ]'.")
            
    def setup_left_pane(self):
        self.dir_frame = ttk.LabelFrame(self.left_pane, text="Project Directory")
        self.dir_frame.pack(fill=tk.X, padx=5, pady=(5, 10))
        self.dir_var = tk.StringVar(value=self.current_dir)
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, state='readonly')
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 2), pady=5)
        self.dir_button = ttk.Button(self.dir_frame, text="Browse...", command=self.select_directory)
        self.dir_button.pack(side=tk.RIGHT, padx=(2, 5), pady=5)

        # --- MODIFIED: Renamed to "Settings & Filters" and added Max Tokens field ---
        self.settings_frame = ttk.LabelFrame(self.left_pane, text="Settings & Filters")
        self.settings_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(self.settings_frame, text="Max Tokens:").grid(row=0, column=0, padx=5, pady=(5,3), sticky='w')
        self.max_tokens_var = tk.StringVar(value="150000")
        self.max_tokens_entry = ttk.Entry(self.settings_frame, textvariable=self.max_tokens_var, width=15)
        self.max_tokens_entry.grid(row=0, column=1, padx=5, pady=(5,3), sticky='w')
        
        ttk.Label(self.settings_frame, text="Include Exts (csv):").grid(row=1, column=0, padx=5, pady=3, sticky='w')
        self.include_ext_var = tk.StringVar(value="py,ts,js,jsx,tsx,vue,html,css,scss,md,json,yaml,sh,rb,go,rs,java,kt,c,cpp,h,cs")
        self.include_ext_entry = ttk.Entry(self.settings_frame, textvariable=self.include_ext_var)
        self.include_ext_entry.grid(row=1, column=1, padx=5, pady=3, sticky='ew')

        ttk.Label(self.settings_frame, text="Exclude Paths (csv):").grid(row=2, column=0, padx=5, pady=3, sticky='w')
        self.exclude_paths_var = tk.StringVar(value="node_modules,.git,.venv,dist,build,__pycache__,*.log,*.tmp,*.bak,*.swp")
        self.exclude_paths_entry = ttk.Entry(self.settings_frame, textvariable=self.exclude_paths_var)
        self.exclude_paths_entry.grid(row=2, column=1, padx=5, pady=3, sticky='ew')

        self.refresh_button = ttk.Button(self.settings_frame, text="Apply Filters & Refresh Tree", command=self.populate_treeview)
        self.refresh_button.grid(row=3, column=0, columnspan=2, pady=(8, 5))
        self.settings_frame.columnconfigure(1, weight=1)
        # --- END OF MODIFICATION ---
        
        self.tree_frame = ttk.LabelFrame(self.left_pane, text="Select Files/Folders")
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(10, 5))
        self.tree = ttk.Treeview(self.tree_frame, columns=("fullpath", "type"), displaycolumns="", show='tree')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set)
        self.tree.bind("<Button-1>", self.on_tree_click, add='+')

    def run_copy_process(self):
        if not tiktoken_available:
            messagebox.showerror("Missing Dependency", "Cannot proceed: tiktoken is not installed.\nPlease run 'pip install tiktoken' and restart.")
            return

        # --- MODIFIED: Read and validate max_tokens from GUI ---
        try:
            max_tokens_limit = int(self.max_tokens_var.get())
            if max_tokens_limit <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Max Tokens must be a positive number.")
            return
        # --- END OF MODIFICATION ---

        selected_files = self.get_selected_file_paths()
        if not selected_files:
            messagebox.showwarning("No Selection", "No files are currently selected.")
            return

        self.clear_summary()
        self.log_message("Starting file processing...")
        self._toggle_buttons(tk.DISABLED)

        # Pass the validated max_tokens_limit to the thread
        thread = threading.Thread(
            target=self._copy_thread_func,
            args=(self.current_dir, selected_files, *self.get_filter_settings(), max_tokens_limit),
            daemon=True
        )
        thread.start()

    # --- MODIFIED: Accept new max_tokens argument ---
    def _copy_thread_func(self, root_dir, selected_paths, include_exts, exclude_paths, max_tokens):
        try:
            _, summary_message = core.generate_prompt_data(
                root_dir, selected_paths, include_exts, exclude_paths, max_tokens
            )
            self.root.after(0, self._update_gui_post_copy, summary_message)
        except Exception as e:
            import traceback
            error_msg = f"An unexpected error occurred during processing: {e}\n{traceback.format_exc()}"
            self.root.after(0, self._update_gui_post_copy, error_msg, True)

    # ... (The rest of the file is unchanged) ...
    def setup_right_pane(self):
        style = ttk.Style()
        try:
            bold_font = (self.default_font.actual('family'), int(self.default_font.actual('size') * 1.1), 'bold')
            style.configure('Accent.TButton', font=bold_font)
        except Exception:
            pass # Font configuration can fail, proceed anyway
        self.copy_button = ttk.Button(self.right_pane, text="Copy Selected to Clipboard", command=self.run_copy_process, style='Accent.TButton')
        self.copy_button.pack(pady=(10, 15), padx=10, fill=tk.X)

        self.summary_frame = ttk.LabelFrame(self.right_pane, text="Summary & Log")
        self.summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text = scrolledtext.ScrolledText(
            self.summary_frame, wrap=tk.WORD, relief=tk.SUNKEN, bd=1, padx=5, pady=5, font=self.text_font
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.configure(state='disabled')

    def log_message(self, message, is_error=False):
        self.summary_text.configure(state='normal')
        tag = "error" if is_error else "info"
        self.summary_text.tag_configure("error", foreground="red")
        self.summary_text.insert(tk.END, message + "\n", (tag,))
        self.summary_text.see(tk.END)
        self.summary_text.configure(state='disabled')

    def select_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.current_dir, title="Select Project Directory")
        if new_dir and os.path.isdir(new_dir):
            self.current_dir = os.path.normpath(new_dir)
            self.dir_var.set(self.current_dir)
            self.populate_treeview()
        elif new_dir:
            messagebox.showwarning("Invalid Selection", f"Path selected is not a valid directory:\n{new_dir}")

    def get_filter_settings(self):
        inc_ext_str = self.include_ext_var.get().strip()
        include_exts = [ext.strip().lstrip('.') for ext in inc_ext_str.split(',') if ext.strip()] if inc_ext_str else None
        exc_path_str = self.exclude_paths_var.get().strip()
        exclude_paths = [path.strip().replace('\\', '/') for path in exc_path_str.split(',') if path.strip()] if exc_path_str else None
        return include_exts, exclude_paths

    def populate_treeview(self):
        self.log_message("Refreshing file tree...")
        for item in self.tree.get_children(): self.tree.delete(item)
        self.checked_state.clear()
        self.tree_items.clear()
        include_exts, exclude_paths = self.get_filter_settings()
        try:
            items = utils.scan_directory(self.current_dir, exclude_paths, include_exts, sort_items=True)
        except Exception as e:
            self.log_message(f"Error scanning directory: {e}", is_error=True)
            return
        parent_map = {'': ''}
        current_scan_rel_paths = set()
        for rel_path, item_type in items:
            current_scan_rel_paths.add(rel_path)
            parent_rel_path = os.path.dirname(rel_path)
            parent_iid = parent_map.get(parent_rel_path, '')
            name = os.path.basename(rel_path)
            initial_state = self.persistent_checked_state.get(rel_path, True)
            self.persistent_checked_state.setdefault(rel_path, initial_state)
            image, text_prefix = (self.img_checked if initial_state else self.img_unchecked, "") if self.img_checked else (None, "[x] " if initial_state else "[ ] ")
            iid = self.tree.insert(parent_iid, 'end', text=f"{text_prefix}{name}", image=image, values=(rel_path, item_type), open=False)
            self.checked_state[iid] = initial_state
            self.tree_items[iid] = (rel_path, item_type)
            if item_type == 'dir':
                parent_map[rel_path] = iid
        stale_paths = set(self.persistent_checked_state.keys()) - current_scan_rel_paths
        for stale_path in stale_paths:
            del self.persistent_checked_state[stale_path]
        self.log_message(f"Tree populated for: {self.current_dir}")
        self.clear_summary()

    def clear_summary(self):
        self.summary_text.configure(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.configure(state='disabled')

    def update_item_visual(self, iid):
        if iid not in self.checked_state: return
        is_checked = self.checked_state[iid]
        if self.img_checked:
            self.tree.item(iid, image=(self.img_checked if is_checked else self.img_unchecked))
        else:
            text = self.tree.item(iid, 'text')
            base_text = text[4:] if text.startswith(("[x] ", "[ ] ")) else text
            self.tree.item(iid, text=("[x] " if is_checked else "[ ] ") + base_text)

    def on_tree_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid: return
        element = self.tree.identify_element(event.x, event.y)
        if self.img_checked and element != 'image': return
        if iid in self.checked_state: self.set_check_state(iid, not self.checked_state[iid], cascade=True)

    def set_check_state(self, iid, state, cascade=True):
        if iid not in self.tree_items: return
        self.checked_state[iid] = state
        self.persistent_checked_state[self.tree_items[iid][0]] = state
        self.update_item_visual(iid)
        if cascade:
            for child_iid in self.tree.get_children(iid):
                self.set_check_state(child_iid, state, cascade=True)

    def get_selected_file_paths(self):
        return [self.tree_items[iid][0] for iid in self.tree_items if self.checked_state.get(iid) and self.tree_items[iid][1] == 'file']

    def _update_gui_post_copy(self, summary_message, is_error=False):
        self.log_message("--- Processing Complete ---", is_error)
        self.log_message(summary_message, is_error)
        self._toggle_buttons(tk.NORMAL)

    def _toggle_buttons(self, state):
        self.refresh_button.config(state=state)
        if tiktoken_available:
            self.copy_button.config(state=state)