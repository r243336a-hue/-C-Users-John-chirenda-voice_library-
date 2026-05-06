"""
Aesthetic and labelled GUI for the voice-navigable library.
Provides visual support for caregivers or low-vision users.
"""

import tkinter as tk
from tkinter import scrolledtext


class LibraryGUI:
    def __init__(self, on_text_search=None, on_play=None, on_pause=None, on_next=None):
        self.on_text_search = on_text_search
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_next = on_next
        self._results = []
        self.root = tk.Tk()
        self.root.title("Voice-Navigable Library")
        self.root.geometry("700x600")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(True, True)

        self.root.attributes("-topmost", True)

        title_font = ("Helvetica", 20, "bold")
        desc_font = ("Helvetica", 11)
        status_font = ("Helvetica", 12, "italic")
        log_font = ("Courier", 10)

        header = tk.Label(
            self.root,
            text="Voice-Navigable Digital Library",
            font=title_font,
            bg="#2c3e50",
            fg="white",
            pady=10,
        )
        header.pack(fill=tk.X)

        desc_frame = tk.Frame(self.root, bg="#34495e", padx=10, pady=10)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)

        desc_label = tk.Label(
            desc_frame,
            text="Support for Visually Impaired Users",
            font=("Helvetica", 12, "bold"),
            bg="#34495e",
            fg="#f1c40f",
        )
        desc_label.pack(anchor=tk.W)

        desc_text = (
            "This library is fully voice-controlled. Use your voice to search, play, pause, resume, and stop books.\n"
            "Example commands: 'play pride and prejudice', 'pause', 'help'\n"
            "All responses are spoken aloud. No visual interaction needed.\n"
            "Alternatively, type a search query below."
        )
        desc_display = tk.Label(
            desc_frame,
            text=desc_text,
            font=desc_font,
            bg="#34495e",
            fg="white",
            justify=tk.LEFT,
            wraplength=550,
        )
        desc_display.pack(anchor=tk.W, pady=5)

        search_frame = tk.Frame(self.root, bg="#2c3e50", pady=5)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            search_frame,
            text="Typing Search:",
            font=("Helvetica", 10, "bold"),
            bg="#2c3e50",
            fg="white",
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.search_entry = tk.Entry(search_frame, font=("Helvetica", 12), width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.search_button = tk.Button(
            search_frame,
            text="Search",
            command=self._on_search_click,
            bg="#1abc9c",
            fg="black",
            font=("Helvetica", 10, "bold"),
        )
        self.search_button.pack(side=tk.RIGHT)

        self.search_entry.bind("<Return>", lambda _e: self._on_search_click())

        self.status_var = tk.StringVar(value="System ready. Say a command or type a search.")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=status_font,
            bg="#1abc9c",
            fg="black",
            pady=8,
        )
        status_label.pack(fill=tk.X, padx=10, pady=5)

        results_label = tk.Label(
            self.root,
            text="Available Books:",
            font=("Helvetica", 10, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        results_label.pack(anchor=tk.W, padx=10)

        self.results_list = tk.Listbox(self.root, height=8, font=("Helvetica", 11))
        self.results_list.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        controls_frame = tk.Frame(self.root, bg="#2c3e50", pady=5)
        controls_frame.pack(fill=tk.X, padx=10)

        self.read_button = tk.Button(
            controls_frame,
            text="Read",
            command=self._on_read_click,
            bg="#3498db",
            fg="white",
            font=("Helvetica", 10, "bold"),
        )
        self.read_button.pack(side=tk.LEFT, padx=(0, 10))

        self.pause_button = tk.Button(
            controls_frame,
            text="Pause",
            command=self._on_pause_click,
            bg="#f39c12",
            fg="black",
            font=("Helvetica", 10, "bold"),
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 10))

        self.next_button = tk.Button(
            controls_frame,
            text="Next",
            command=self._on_next_click,
            bg="#2ecc71",
            fg="black",
            font=("Helvetica", 10, "bold"),
        )
        self.next_button.pack(side=tk.LEFT)

        log_label = tk.Label(
            self.root,
            text="Activity Log:",
            font=("Helvetica", 10, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        log_label.pack(anchor=tk.W, padx=10)

        self.log_area = scrolledtext.ScrolledText(
            self.root,
            height=12,
            font=log_font,
            bg="#ecf0f1",
            fg="black",
            state=tk.NORMAL,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_area.insert(tk.END, "Waiting for voice commands or typed searches...\n")
        self.log_area.config(state=tk.DISABLED)

        footer = tk.Label(
            self.root,
            text="All audio feedback is spoken. Close this window to exit.",
            font=("Helvetica", 9),
            bg="#2c3e50",
            fg="#bdc3c7",
            pady=5,
        )
        footer.pack(side=tk.BOTTOM, fill=tk.X)

    def set_results(self, books):
        self._results = books or []
        self.results_list.delete(0, tk.END)
        for book in self._results:
            title = book.get("title", "Untitled")
            author = book.get("author") or "Unknown"
            self.results_list.insert(tk.END, f"{title} — {author}")

    def _on_search_click(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        self.add_log_entry(f"[Typed search] {query}")
        if self.on_text_search:
            self.on_text_search(query)
        self.search_entry.delete(0, tk.END)

    def _on_read_click(self):
        selection = self.results_list.curselection()
        if not selection:
            return
        book = self._results[selection[0]]
        if self.on_play:
            self.on_play(book)

    def _on_pause_click(self):
        if self.on_pause:
            self.on_pause()

    def _on_next_click(self):
        if self.on_next:
            self.on_next()

    def update_status(self, message):
        def _update():
            self.status_var.set(message)
        self.root.after(0, _update)

    def add_log_entry(self, entry):
        def _add():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, entry + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, _add)

    def start(self):
        self.root.mainloop()

    def stop(self):
        self.root.quit()
        self.root.destroy()
