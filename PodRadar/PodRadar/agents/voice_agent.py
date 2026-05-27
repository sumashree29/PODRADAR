# voice_agent.py
# Clean text-only popup. No voice, no Whisper, no mic dependencies.

import tkinter as tk
from tkinter import font as tkfont

def show_popup():
    """
    Opens the PodRadar floating popup.
    Returns the query string on Submit, or None if closed.
    """
    result = {"query": None}

    root = tk.Tk()
    root.title("PodRadar")
    root.geometry("480x180")
    root.resizable(False, False)
    root.configure(bg="#0f0f0f")
    root.attributes("-topmost", True)

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw // 2) - 240
    y = (sh // 2) - 90
    root.geometry(f"480x180+{x}+{y}")

    title_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
    label_font = tkfont.Font(family="Segoe UI", size=9)
    btn_font   = tkfont.Font(family="Segoe UI", size=9, weight="bold")

    tk.Label(root, text="🎙 PodRadar", font=title_font,
             bg="#0f0f0f", fg="#00d4aa").pack(pady=(16, 2))
    tk.Label(root, text="Type your request and press Enter or Submit",
             font=label_font, bg="#0f0f0f", fg="#888888").pack()

    entry_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=entry_var, width=52,
                     font=label_font, bg="#1e1e1e", fg="#ffffff",
                     insertbackground="#00d4aa", relief="flat",
                     highlightthickness=1, highlightbackground="#333333",
                     highlightcolor="#00d4aa")
    entry.pack(pady=(12, 8), ipady=6)
    entry.focus()

    status_var = tk.StringVar(value="")
    tk.Label(root, textvariable=status_var,
             font=label_font, bg="#0f0f0f", fg="#ffaa00").pack()

    def on_submit():
        query = entry_var.get().strip()
        if query:
            result["query"] = query
            root.destroy()

    tk.Button(root, text="▶ Submit", command=on_submit,
              font=btn_font, bg="#00d4aa", fg="#0f0f0f",
              activebackground="#00b898", relief="flat",
              padx=20, pady=6, cursor="hand2").pack()

    root.bind("<Return>", lambda e: on_submit())
    root.bind("<Escape>", lambda e: root.destroy())

    root.mainloop()
    return result["query"]


if __name__ == "__main__":
    query = show_popup()
    print(f"Query returned: {query}")