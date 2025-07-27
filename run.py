# run.py
import tkinter as tk
from promptgen_gui.app import PromptgenGUI, ttk_themes_available

# This file serves as the main entry point for the application.
# Running this script from the root directory ensures that all module imports
# within the 'promptgen_gui' package work correctly without path manipulation.

def main():
    """Initializes and runs the PromptGen GUI application."""
    if ttk_themes_available:
        try:
            from ttkthemes import ThemedTk
            root = ThemedTk(theme="arc")
        except (ImportError, tk.TclError):
            # Fallback if theme isn't found or ttkthemes is installed but broken
            root = tk.Tk()
    else:
        root = tk.Tk()

    app = PromptgenGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()