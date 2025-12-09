#######
###
### Hopufully simple and clean main file with GUI and little to no logic
###
#######



import customtkinter
from utils import get_all_files, get_dict_of_hashes, find_duplicates, save_duplicates_to_file, filter_files_by_extension
import os
from PIL import Image
from PIL import ImageTk
import os


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
        
        self.prev_key_button = customtkinter.CTkButton(master=nav_frame, text="< Previous File", command=self.prev_key)
        self.prev_key_button.pack(side="left", padx=10)
        
        self.key_label = customtkinter.CTkLabel(master=nav_frame, text="")
        self.key_label.pack(side="left", padx=10)
        
        self.next_key_button = customtkinter.CTkButton(master=nav_frame, text="Next File >", command=self.next_key)
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
        
        for widget in self.left_frame.winfo_children():
            widget.destroy()
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
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
                
                try:
                    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        img = Image.open(file_path)
                        img.thumbnail((400, 400))
                        photo = ImageTk.PhotoImage(img)
                        img_label = customtkinter.CTkLabel(master=frame, image=photo, text="")
                        img_label.image = photo
                        img_label.pack(padx=10, pady=10)
                    else:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(500)
                        text_label = customtkinter.CTkLabel(master=frame, text=content, wraplength=350, justify="left")
                        text_label.pack(padx=10, pady=10)
                except Exception as e:
                    error_label = customtkinter.CTkLabel(master=frame, text=f"Error loading file: {str(e)}")
                    error_label.pack(padx=10, pady=10)

    def delete_file(self):
        current_key = self.keys[self.current_key_index]
        files = self.duplicates_dict[current_key]
        if self.current_file_index + 1 < len(files):
            file_to_delete = files[self.current_file_index + 1]
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
                print(f"Error deleting file: {str(e)}")

    def next_file(self):
        current_key = self.keys[self.current_key_index]
        files = self.duplicates_dict[current_key]
        if self.current_file_index + 2 < len(files):
            self.current_file_index += 1
        self.load_files()

    def prev_key(self):
        if self.current_key_index > 0:
            self.current_key_index -= 1
            self.current_file_index = 0
        self.load_files()

    def next_key(self):
        if self.current_key_index < len(self.keys) - 1:
            self.current_key_index += 1
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

    
    def select_directory(self):
        from tkinter import filedialog

        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.directory_input_box.configure(state="normal")
            self.directory_input_box.delete(0, customtkinter.END)
            self.directory_input_box.insert(0, selected_directory)
            self.directory_input_box.configure(state="disabled")

    def start_scan(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        if self.comparison_frame:
            self.comparison_frame.destroy()
            self.comparison_frame = None

        directory = self.directory_input_box.get()
        try:
            file_paths = get_all_files(directory)
            dict_of_hashes = get_dict_of_hashes(file_paths)
            duplicates = find_duplicates(dict_of_hashes)
            if duplicates:
                save_duplicates_to_file(duplicates)
                self.show_results("Duplicates found.", duplicates_found=True)
            else:
                self.show_results("No duplicate files were found.", duplicates_found=False)
                
        except ValueError as ve:
            self.show_results(f"Error: {str(ve)}", duplicates_found=False)
    
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
        import os
        import platform
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
        

app = App()
app.mainloop()