#######
###
### Hopufully simple and clean main file with GUI and little to no logic
###
#######


import os
import platform
import queue
import threading
from tkinter import filedialog, messagebox

import customtkinter
from PIL import Image, ImageTk

from utils import (
    ScanCancelled,
    filter_files_by_extension,
    is_image,
    is_text,
    save_duplicates_to_file,
    scan_for_duplicates,
)

STAGE_LABELS = {
    "list": "Looking for files...",
    "size": "Checking file sizes",
    "quick": "Quick hash comparison",
    "full": "Full hash comparison",
}


def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


class ComparisonFrame(customtkinter.CTkFrame):
    def __init__(self, master, duplicates_dict, on_close_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.duplicates_dict = duplicates_dict
        self.keys = list(duplicates_dict.keys())
        self.current_key_index = 0
        self.current_file_index = 0
        self.on_close_callback = on_close_callback

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Navigation buttons for keys
        nav_frame = customtkinter.CTkFrame(master=self)
        nav_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        self.prev_key_button = customtkinter.CTkButton(master=nav_frame, text="< Previous File", command=lambda: self.move_key(-1))
        self.prev_key_button.pack(side="left", padx=10)

        self.key_label = customtkinter.CTkLabel(master=nav_frame, text="")
        self.key_label.pack(side="left", padx=10)

        self.next_key_button = customtkinter.CTkButton(master=nav_frame, text="Next File >", command=lambda: self.move_key(1))
        self.next_key_button.pack(side="left", padx=10)

        # File display frames
        self.left_frame = customtkinter.CTkFrame(master=self)
        self.left_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.right_frame = customtkinter.CTkFrame(master=self)
        self.right_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        # Action buttons
        action_frame = customtkinter.CTkFrame(master=self)
        action_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self.delete_button = customtkinter.CTkButton(master=action_frame, text="Delete Right File", fg_color="red", command=self.delete_file)
        self.delete_button.pack(side="left", padx=10)

        self.next_file_button = customtkinter.CTkButton(master=action_frame, text="Next File Pair", command=self.next_file)
        self.next_file_button.pack(side="left", padx=10)

        self.load_files()

    def load_files(self):

        clear_frame(self.left_frame)
        clear_frame(self.right_frame)

        if not self.keys or self.current_key_index >= len(self.keys):
            if not self.keys and self.on_close_callback:
                self.on_close_callback()
            return

        current_key = self.keys[self.current_key_index]
        files = self.duplicates_dict[current_key]
        self.key_label.configure(text=f"Hash: {current_key[:16]}... ({self.current_file_index + 1}/{len(files) - 1})")

        if self.current_file_index + 1 < len(files):
            for i, frame in enumerate([self.left_frame, self.right_frame]):
                file_path = files[i + self.current_file_index]
                label = customtkinter.CTkLabel(master=frame, text=file_path, wraplength=300)
                label.pack(padx=10, pady=10)
                self.add_preview(frame, file_path)

    def add_preview(self, frame, file_path):
        try:
            if is_image(file_path):
                img = Image.open(file_path)
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                img_label = customtkinter.CTkLabel(master=frame, image=photo, text="")
                img_label.image = photo
                img_label.pack(padx=10, pady=10)
            elif is_text(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(500)
                text_label = customtkinter.CTkLabel(master=frame, text=content, wraplength=350, justify="left")
                text_label.pack(padx=10, pady=10)
            else:
                info_label = customtkinter.CTkLabel(master=frame, text="Preview not available for this file type.")
                info_label.pack(padx=10, pady=10)
        except Exception as e:
            error_label = customtkinter.CTkLabel(master=frame, text=f"Error loading file: {str(e)}")
            error_label.pack(padx=10, pady=10)

    def delete_file(self):
        current_key = self.keys[self.current_key_index]
        files = self.duplicates_dict[current_key]
        if self.current_file_index + 1 < len(files):
            file_to_delete = files[self.current_file_index + 1]
            if not messagebox.askyesno("Delete file", f"Permanently delete this file?\n\n{file_to_delete}"):
                return
            try:
                os.remove(file_to_delete)
                files.pop(self.current_file_index + 1)

                # Se ci sono ancora file duplicati con lo stesso hash, rimani sullo stesso indice
                # Altrimenti passa al prossimo hash
                if len(files) <= 1:  # Solo il file originale rimane
                    # Rimuovi questo hash dalla lista
                    self.keys.pop(self.current_key_index)
                    del self.duplicates_dict[current_key]

                    # Se non ci sono più hash, chiudi la finestra
                    if not self.keys:
                        if self.on_close_callback:
                            self.on_close_callback()
                        return

                    # Se siamo alla fine, vai all'hash precedente
                    if self.current_key_index >= len(self.keys):
                        self.current_key_index = len(self.keys) - 1

                    self.current_file_index = 0
                else:
                    # Se l'indice corrente è oltre l'ultimo file, torna indietro
                    if self.current_file_index + 1 >= len(files):
                        self.current_file_index = max(0, len(files) - 2)

                self.load_files()
            except Exception as e:
                messagebox.showerror("Delete file", f"Error deleting file: {str(e)}")

    def next_file(self):
        current_key = self.keys[self.current_key_index]
        files = self.duplicates_dict[current_key]
        if self.current_file_index + 2 < len(files):
            self.current_file_index += 1
        self.load_files()

    def move_key(self, delta):
        next_index = self.current_key_index + delta
        if 0 <= next_index < len(self.keys):
            self.current_key_index = next_index
            self.current_file_index = 0
        self.load_files()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Duplicate Terminator")
        self.geometry("1200x800")

        self.grid_rowconfigure(0, weight=1)  # configure grid system
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3) # Comparison area gets more space

        # Left Panel (Input + Results)
        self.left_panel = customtkinter.CTkFrame(master=self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_panel.grid_rowconfigure(2, weight=1) # Allow results to expand if needed

        # Input Section
        self.directory_input_box = customtkinter.CTkEntry(master=self.left_panel, placeholder_text="Select a directory to scan")
        self.directory_input_box.configure(state="disabled")
        self.directory_input_box.pack(padx=20, pady=(20, 10), fill="x")

        self.select_directory_button = customtkinter.CTkButton(master=self.left_panel, text="Select Directory", command=self.select_directory)
        self.select_directory_button.pack(padx=20, pady=10)

        self.start_scan_button = customtkinter.CTkButton(master=self.left_panel, text="Start Scan", command=self.start_scan)
        self.start_scan_button.pack(padx=20, pady=10)

        # Results Section (Container)
        self.results_frame = customtkinter.CTkFrame(master=self.left_panel, fg_color="transparent")
        self.results_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.comparison_frame = None
        self.filtered = None
        self.scan_queue = None
        self.scan_thread = None
        self.scan_cancel_event = None

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def select_directory(self):
        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.directory_input_box.configure(state="normal")
            self.directory_input_box.delete(0, customtkinter.END)
            self.directory_input_box.insert(0, selected_directory)
            self.directory_input_box.configure(state="disabled")

    def start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return

        directory = self.directory_input_box.get()
        if not directory:
            self.show_results("Select a directory first.")
            return

        # Clear previous results
        clear_frame(self.results_frame)
        if self.comparison_frame:
            self.comparison_frame.destroy()
            self.comparison_frame = None

        self.progress_label = customtkinter.CTkLabel(master=self.results_frame, text="Starting scan...", wraplength=250)
        self.progress_label.pack(padx=20, pady=10)
        self.progress_bar = customtkinter.CTkProgressBar(master=self.results_frame)
        self.progress_bar.pack(padx=20, pady=10, fill="x")
        self.progress_bar.set(0)
        self.cancel_scan_button = customtkinter.CTkButton(master=self.results_frame, text="Cancel Scan", fg_color="red", command=self.cancel_scan)
        self.cancel_scan_button.pack(padx=20, pady=10)

        self.scan_cancel_event = threading.Event()
        self.scan_queue = queue.Queue()
        self.scan_thread = threading.Thread(target=self.scan_worker, args=(directory,), daemon=True)
        self.scan_thread.start()
        self.after(100, self.poll_scan_queue)

    def cancel_scan(self):
        if self.scan_cancel_event:
            self.scan_cancel_event.set()

    def scan_worker(self, directory):
        results = self.scan_queue
        try:
            duplicates = scan_for_duplicates(
                directory,
                progress_callback=lambda stage, done, total, path: results.put(("progress", stage, done, total, path)),
                should_stop=lambda: self.scan_cancel_event.is_set(),
            )
        except ScanCancelled:
            results.put(("cancelled",))
        except ValueError as error:
            results.put(("error", str(error)))
        else:
            results.put(("done", duplicates))

    def poll_scan_queue(self):
        terminal_message = None
        try:
            while True:
                message = self.scan_queue.get_nowait()
                if message[0] == "progress":
                    self.update_scan_progress(*message[1:])
                else:
                    terminal_message = message
                    break
        except queue.Empty:
            pass

        if terminal_message is None:
            self.after(100, self.poll_scan_queue)
            return

        for widget in (self.progress_label, self.progress_bar, self.cancel_scan_button):
            widget.destroy()

        if terminal_message[0] == "done":
            self.scan_finished(terminal_message[1])
        elif terminal_message[0] == "cancelled":
            self.show_results("Scan cancelled.")
        elif terminal_message[0] == "error":
            self.show_results(f"Error: {terminal_message[1]}")

    def update_scan_progress(self, stage, done, total, path):
        label = STAGE_LABELS.get(stage, stage)
        text = f"{label} ({done}/{total})" if total else label
        if path:
            text += f"\n{path}"
        self.progress_label.configure(text=text)
        if stage != "list" and total:
            self.progress_bar.set(done / total)

    def scan_finished(self, duplicates):
        if duplicates:
            save_duplicates_to_file(duplicates)
            self.show_results("Duplicates found.", duplicates_found=True)
        else:
            self.show_results("No duplicate files were found.", duplicates_found=False)

    def show_results(self, message, duplicates_found=False):
        label = customtkinter.CTkLabel(master=self.results_frame, text=message, wraplength=250)
        label.pack(pady=10)

        if duplicates_found:
            open_btn = customtkinter.CTkButton(master=self.results_frame, text="Open Duplicates File", command=self.open_duplicates_file)
            open_btn.pack(pady=10)

            info_label = customtkinter.CTkLabel(master=self.results_frame, text="You can open some file directly from here and choose what to keep:", wraplength=250)
            info_label.pack(pady=10)

            check_btn = customtkinter.CTkButton(master=self.results_frame, text="Check compatible Duplicates File", command=self.check_compability)
            check_btn.pack(pady=10)

            self.start_comparison_button = customtkinter.CTkButton(master=self.results_frame, text="Start Comparison", command=self.start_comparison)
            # Button is created but not packed until check is done, similar to original logic

    def open_duplicates_file(self):
        duplicates_file_path = os.path.abspath('duplicates.txt')
        if platform.system() == 'Windows':
            os.startfile(duplicates_file_path)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{duplicates_file_path}"')
        else:  # Linux and others
            os.system(f'xdg-open "{duplicates_file_path}"')

    def check_compability(self):
        filtered_files = filter_files_by_extension()
        if filtered_files:
            self.filtered = filtered_files
            self.start_comparison_button.pack(pady=10)

            lbl = customtkinter.CTkLabel(master=self.results_frame, text="Compatible files found! Click 'Start Comparison' to review them.", wraplength=250)
            lbl.pack(pady=5)
        else:
            lbl = customtkinter.CTkLabel(master=self.results_frame, text="No compatible files found for comparison.", wraplength=250)
            lbl.pack(pady=5)

    def start_comparison(self):
        if self.filtered:
            if self.comparison_frame:
                self.comparison_frame.destroy()

            self.comparison_frame = ComparisonFrame(master=self, duplicates_dict=self.filtered, on_close_callback=self.on_comparison_close)
            self.comparison_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def on_comparison_close(self):
        if self.comparison_frame:
            self.comparison_frame.destroy()
            self.comparison_frame = None

        lbl = customtkinter.CTkLabel(master=self.results_frame, text="Comparison finished.", wraplength=250)
        lbl.pack(pady=5)

    def on_window_close(self):
        self.cancel_scan()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
