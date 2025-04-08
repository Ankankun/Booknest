# --- START OF main.py ---

from PIL import Image, ImageTk # Note: We might use CTkImage directly later
from io import BytesIO
import requests
import json
import customtkinter as ctk
import os
from tkinter import ttk, messagebox # Keep ttk for Treeview, messagebox for popups
from functools import partial
import pymysql
import customs as cs         # Still used for column tuples
import credentials as cr     # Database credentials

# --- CTk Settings ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class Management:
    """
    Main class for the Library Management System application using CustomTkinter.
    Handles UI setup, user interactions, and database operations.
    """
    def __init__(self, root):
        """
        Initializes the main application window and its core layout frames.
        Args:
            root (ctk.CTk): The main CustomTkinter window instance.
        """
        self.window = root
        self.window.title("Library Management System (CTk)")
        self.window.geometry("1366x768")
        self.window.resizable(True, True)

        # --- Fonts (Using CTkFont) ---
        self.heading_font = ctk.CTkFont(family="Helvetica", size=20, weight="bold")
        self.label_font = ctk.CTkFont(family="Helvetica", size=13, weight="bold")
        self.entry_font = ctk.CTkFont(family="Arial", size=13)
        self.button_font = ctk.CTkFont(family="Helvetica", size=12, weight="bold")
        self.status_font = ctk.CTkFont(family="Arial", size=10)
        self.tree_heading_font = ctk.CTkFont(family="Helvetica", size=11, weight="bold")

        self.style = ttk.Style()
        self._configure_treeview_style()

        self.window.protocol("WM_DELETE_WINDOW", self.Exit)

        # --- Main Layout Frames using Grid ---
        self.window.grid_columnconfigure(0, weight=3) # Content area
        self.window.grid_columnconfigure(1, weight=1) # Action panel
        self.window.grid_rowconfigure(0, weight=1)    # Main content row
        self.window.grid_rowconfigure(1, weight=0)    # Status bar row

        # --- Left Frame (Content Area) ---
        self.frame_1 = ctk.CTkFrame(self.window, corner_radius=10)
        self.frame_1.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        self.frame_1.grid_rowconfigure(0, weight=1)
        self.frame_1.grid_columnconfigure(0, weight=1)

        # --- Right Frame (Action Panel) ---
        self.frame_2 = ctk.CTkFrame(self.window, corner_radius=10)
        self.frame_2.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        self.frame_2.grid_columnconfigure((0, 1), weight=1, uniform="btn_col")

        # --- Action Buttons (in frame_2) ---
        button_opts = {'font': self.button_font, 'corner_radius': 8,
                       'border_spacing': 2, 'height': 35 }
        grid_opts = {'pady': 8, 'padx': 8, 'sticky': 'ew'}
        buttons_config = [
            ('Add Book', self.AddNewBook, None, 0, 0),
            ('Search Book', self.GetBookNametoSearch, None, 0, 1),
            ('Issue Book', self.GetData_for_IssueBook, "orange", 1, 0),
            ('Book Holders', self.AllBorrowRecords, None, 1, 1),
            ('Return Book', self.ReturnBook, "green", 2, 0),
            ('All Books', self.ShowBooks, None, 2, 1),
            ('Clear Screen', self.ClearScreen, "red", 3, 0),
            ('Exit', self.Exit, None, 3, 1),
        ]
        for text, cmd, color, row, col in buttons_config:
            btn_fg_color = color if color else None
            btn = ctk.CTkButton(self.frame_2, text=text, command=cmd, fg_color=btn_fg_color, **button_opts)
            btn.grid(row=row, column=col, **grid_opts)

        # --- Frame 3 (Contextual Actions) ---
        self.frame_3 = ctk.CTkFrame(self.frame_2, fg_color="transparent", corner_radius=0)
        self.frame_3.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(20, 5))
        self.frame_3.grid_columnconfigure((0, 1), weight=1, uniform="ctx_btn_col")

        # --- Status Bar ---
        self.status_bar = ctk.CTkLabel(self.window, text="Welcome!", height=20,
                                       font=self.status_font, anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0,5))

        self.ShowWelcomeMessage()

    # --- Style Configuration ---
    def _configure_treeview_style(self):
        """Configures ttk.Treeview style to better match the CustomTkinter theme."""
        bg_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        heading_bg_color = self.window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"])

        self.style.theme_use('default')
        self.style.configure("Treeview", background=bg_color, foreground=text_color,
                             fieldbackground=bg_color, rowheight=25,
                             bordercolor=heading_bg_color, borderwidth=1)
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        self.style.configure("Treeview.Heading", background=heading_bg_color, foreground=text_color,
                             font=self.tree_heading_font, relief="flat", padding=(5, 5))
        self.style.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])
        self.style.configure("Vertical.TScrollbar", background=bg_color, troughcolor=heading_bg_color)
        self.style.configure("Horizontal.TScrollbar", background=bg_color, troughcolor=heading_bg_color)

    # --- Helper Methods ---
    def _connect_db(self):
        """Establishes and returns a database connection and cursor."""
        try:
            connection = pymysql.connect(host=cr.host, user=cr.user, password=cr.password, database=cr.database, connect_timeout=5) # Added timeout
            cursor = connection.cursor()
            return connection, cursor
        except pymysql.Error as e:
            self.UpdateStatusBar(f"Database Connection Error: {e}")
            messagebox.showerror("Database Error", f"Could not connect to the database.\nError: {e}", parent=self.window)
            return None, None

    def _close_db(self, connection):
        """Closes the database connection if it's open."""
        if connection and connection.open:
            connection.close()

    def UpdateStatusBar(self, text):
        """Updates the text in the status bar."""
        self.status_bar.configure(text=text)

    def ClearScreen(self):
        """Removes widgets from frame_1 and frame_3, resets status bar."""
        for widget in self.frame_1.winfo_children():
            widget.destroy()
        for widget in self.frame_3.winfo_children():
            widget.destroy()
        self.UpdateStatusBar("Ready.")

        # Inside the Management class

    def ShowWelcomeMessage(self):  
        """Displays a welcome message with a background image in frame_1."""  
        self.ClearScreen()  
        self.UpdateStatusBar("Welcome! Select an action.")  
        # Load background image  
        try:  
            script_dir = os.path.dirname(__file__)  
            image_path = os.path.join(script_dir, "background.jpg")  # Ensure we are using the correct path  

            original_image = Image.open(image_path)  
            
            # Get frame dimensions after update  
            self.frame_1.update_idletasks()  
            frame_width = self.frame_1.winfo_width()  
            frame_height = self.frame_1.winfo_height()  

            # Resize based on aspect ratio  
            img_aspect_ratio = original_image.height / original_image.width  
            
            if frame_width > frame_height * img_aspect_ratio:  
                new_width = frame_height / img_aspect_ratio  
                new_height = frame_height  
            else:  
                new_width = frame_width  
                new_height = frame_width * img_aspect_ratio  

            resized_image = original_image.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)  

            # Create a CTkImage  
            self.bg_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image,  
                                        size=(resized_image.width, resized_image.height))  
            self.bg_label = ctk.CTkLabel(self.frame_1, text="", image=self.bg_image)  
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)  

        except FileNotFoundError:  
            print(f"Background image not found at {image_path}. Displaying solid color.")  
            self.bg_label = None  
        except Exception as e:  
            print(f"Error loading background image: {e}")  
            self.bg_label = None  

        # Position title and subtitle   
        title_label = ctk.CTkLabel(self.frame_1,  
                                    text="Library Management System",  
                                    font=ctk.CTkFont(family="Helvetica", size=36, weight="bold"),  
                                    fg_color="transparent",  
                                    text_color=("gray10", "gray90"))  
        title_label.place(relx=0.5, rely=0.4, anchor="center")  

        subtitle_label = ctk.CTkLabel(self.frame_1,  
                                    text="Select an action from the right panel to begin.",  
                                    font=ctk.CTkFont(family="Arial", size=16),  
                                    fg_color="transparent",  
                                    text_color=("gray10", "gray90"))  
        subtitle_label.place(relx=0.5, rely=0.5, anchor="center")  

    # --- Form Reset Methods ---
    def reset_add_book_fields(self):
        """Clears fields in the Add Book form."""
        if hasattr(self, 'isbn_entry'): self.isbn_entry.delete(0, ctk.END)
        if hasattr(self, 'id_entry'): self.id_entry.delete(0, ctk.END)
        if hasattr(self, 'bookname_entry'): self.bookname_entry.delete(0, ctk.END)
        if hasattr(self, 'author_entry'): self.author_entry.delete(0, ctk.END)
        if hasattr(self, 'edition_entry'): self.edition_entry.delete(0, ctk.END)
        if hasattr(self, 'price_entry'): self.price_entry.delete(0, ctk.END)
        if hasattr(self, 'qty_entry'): self.qty_entry.delete(0, ctk.END)
        if hasattr(self, 'isbn_entry'): self.isbn_entry.focus() # Focus ISBN first

    def reset_issue_book_fields(self):
        """Clears fields in the Issue Book form."""
        if hasattr(self, 'book_id_entry'): self.book_id_entry.delete(0, ctk.END)
        if hasattr(self, 'book_name_entry'): self.book_name_entry.delete(0, ctk.END)
        if hasattr(self, 'stu_roll_entry'): self.stu_roll_entry.delete(0, ctk.END)
        if hasattr(self, 'stu_name_entry'): self.stu_name_entry.delete(0, ctk.END)
        if hasattr(self, 'course_entry'): self.course_entry.delete(0, ctk.END)
        if hasattr(self, 'subject_entry'): self.subject_entry.delete(0, ctk.END)
        if hasattr(self, 'issue_date_entry'): self.issue_date_entry.delete(0, ctk.END)
        if hasattr(self, 'return_date_entry'): self.return_date_entry.delete(0, ctk.END)
        if hasattr(self, 'book_id_entry'): self.book_id_entry.focus()

    # --- Treeview Creation Helper ---
    def _create_treeview(self, parent_frame, columns_config, data_columns):
        """Creates and configures a Treeview widget with scrollbars."""
        tree_container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, pady=(10, 0))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        scroll_x = ttk.Scrollbar(tree_container, orient='horizontal', style="Horizontal.TScrollbar")
        scroll_y = ttk.Scrollbar(tree_container, orient='vertical', style="Vertical.TScrollbar")

        tree = ttk.Treeview(tree_container, columns=data_columns, height=18,
                            selectmode="browse", yscrollcommand=scroll_y.set,
                            xscrollcommand=scroll_x.set, show='headings', style="Treeview")

        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)

        tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')

        for col_id, text, width, anchor in columns_config:
            # Use string 'w', 'e', 'center' directly for anchor
            real_anchor = anchor if isinstance(anchor, str) else 'w'
            tree.heading(col_id, text=text, anchor=real_anchor)
            tree.column(col_id, width=width, anchor=real_anchor, stretch=True)

        return tree

    # --- API Fetch Function ---
    def _fetch_book_details_from_api(self):
        """Fetches book details AND cover image from Open Library API based on ISBN."""
        isbn = self.isbn_entry.get().strip()
        if not isbn or not (len(isbn) == 10 or len(isbn) == 13) or not isbn.replace('-', '').isdigit():
            messagebox.showerror("Input Error", "Please enter a valid 10 or 13 digit ISBN.", parent=self.window)
            self.UpdateStatusBar("Invalid ISBN format entered.")
            self._clear_cover_image() # Clear cover on error too
            return

        OPENLIBRARY_URL = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        self.UpdateStatusBar(f"Fetching details for ISBN: {isbn}...")
        self._clear_cover_image() # Clear previous cover before fetching new one
        self.cover_label.configure(text="Loading...") # Indicate loading

        try:
            response = requests.get(OPENLIBRARY_URL, timeout=15)
            response.raise_for_status()
            data = response.json()

            isbn_key = f"ISBN:{isbn}"
            if isbn_key not in data or not data[isbn_key]:
                messagebox.showinfo("Not Found", f"No book details found for ISBN: {isbn} on Open Library.", parent=self.window)
                self.UpdateStatusBar(f"ISBN {isbn} not found via API.")
                self._clear_cover_image()
                return

            book_data = data[isbn_key]

            # --- Extract Text Data (Same as before) ---
            title = book_data.get("title", "N/A")
            authors_list = book_data.get("authors", [])
            authors_str = ", ".join([author.get("name", "") for author in authors_list if author.get("name")]) or "N/A"
            publishers_list = book_data.get("publishers", [])
            publishers_str = ", ".join([pub.get("name", "") for pub in publishers_list if pub.get("name")])
            publish_date = book_data.get("publish_date", "")
            edition_str = f"{publishers_str}, {publish_date}".strip(', ') or "N/A"
            price_str = ""

            # --- Auto-fill Text Fields (Same as before) ---
            self.bookname_entry.delete(0, ctk.END); self.bookname_entry.insert(0, title)
            self.author_entry.delete(0, ctk.END); self.author_entry.insert(0, authors_str)
            self.edition_entry.delete(0, ctk.END); self.edition_entry.insert(0, edition_str)
            self.price_entry.delete(0, ctk.END)
            self.id_entry.delete(0, ctk.END); self.id_entry.insert(0, isbn)
            if not self.qty_entry.get(): self.qty_entry.insert(0, "1")

            # --- Fetch and Display Cover Image ---
            cover_url = None
            if "cover" in book_data:
                # Prefer medium or large covers if available
                if "medium" in book_data["cover"]:
                    cover_url = book_data["cover"]["medium"]
                elif "large" in book_data["cover"]:
                    cover_url = book_data["cover"]["large"]
                elif "small" in book_data["cover"]: # Fallback to small
                    cover_url = book_data["cover"]["small"]

            if cover_url:
                self.UpdateStatusBar(f"Details fetched. Fetching cover image...")
                try:
                    # Download the image data
                    img_response = requests.get(cover_url, timeout=10, stream=True) # Use stream for potentially large files
                    img_response.raise_for_status() # Check if image download worked

                    # Ensure content type looks like an image
                    content_type = img_response.headers.get('content-type')
                    if not content_type or not content_type.lower().startswith('image/'):
                         raise ValueError(f"URL did not return an image (Content-Type: {content_type})")

                    # Open image data using Pillow from BytesIO stream
                    image_bytes = BytesIO(img_response.content)
                    pil_image = Image.open(image_bytes)

                    # --- Resize the image ---
                    # Define desired display size
                    display_width = 140
                    aspect_ratio = pil_image.height / pil_image.width
                    display_height = int(display_width * aspect_ratio)
                    # Cap max height
                    max_height = 200
                    if display_height > max_height:
                        display_height = max_height
                        display_width = int(display_height / aspect_ratio)

                    pil_image_resized = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

                    # Create CTkImage object
                    ctk_image = ctk.CTkImage(light_image=pil_image_resized,
                                             dark_image=pil_image_resized, # Use same image for both modes
                                             size=(display_width, display_height))

                    # Update the label with the image
                    self.cover_label.configure(image=ctk_image, text="") # Set image, clear text
                    self.UpdateStatusBar(f"Details and cover fetched for '{title}'.")

                except requests.exceptions.RequestException as img_err:
                    print(f"Error fetching cover image: {img_err}")
                    self.cover_label.configure(image=None, text="Cover Error")
                    self.UpdateStatusBar(f"Details fetched, but failed to load cover image.")
                except (IOError, Image.UnidentifiedImageError) as img_proc_err:
                     print(f"Error processing cover image: {img_proc_err}")
                     self.cover_label.configure(image=None, text="Bad Image")
                     self.UpdateStatusBar(f"Details fetched, but failed to process cover image.")
                except Exception as img_other_err:
                     print(f"Unexpected error with cover image: {img_other_err}")
                     self.cover_label.configure(image=None, text="Cover Error")
                     self.UpdateStatusBar(f"Details fetched, error loading cover.")

            else:
                # No cover URL found in API data
                self._clear_cover_image() # Reset to placeholder
                self.cover_label.configure(text="No Cover Found")
                self.UpdateStatusBar(f"Details fetched for '{title}'. No cover image available.")

        # --- Main Error Handling (Same as before) ---
        except requests.exceptions.Timeout:
            messagebox.showerror("API Error", "The request to Open Library timed out.", parent=self.window)
            self.UpdateStatusBar("API request timed out.")
            self._clear_cover_image()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Could not fetch data from Open Library:\n{e}", parent=self.window)
            self.UpdateStatusBar("API request failed.")
            self._clear_cover_image()
        except json.JSONDecodeError:
            messagebox.showerror("API Error", "Received an invalid response from Open Library.", parent=self.window)
            self.UpdateStatusBar("Error parsing API response.")
            self._clear_cover_image()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during fetch:\n{e}", parent=self.window)
            self.UpdateStatusBar("Unexpected error during fetch.")
            self._clear_cover_image()

    # 1. Add New Book (Modified for Cover Display)
    def AddNewBook(self):
        """Displays the form to add a new book, includes ISBN fetch and cover preview."""
        self.ClearScreen()
        self.UpdateStatusBar("Enter ISBN to fetch details, or fill manually.")

        container_frame = ctk.CTkFrame(self.frame_1)
        container_frame.pack(pady=20, padx=30, fill="x", expand=False)
        # Configure columns: 0 for labels, 1 for entries, 2 for fetch btn/spacing, 3 for cover
        container_frame.grid_columnconfigure(1, weight=1) # Let entry column expand
        container_frame.grid_columnconfigure(3, weight=0, minsize=150) # Fixed space for cover

        ctk.CTkLabel(container_frame, text="Add New Book", font=self.heading_font).grid(row=0, column=0, columnspan=4, pady=(10, 25), sticky="ew")

        # --- ISBN Row ---
        ctk.CTkLabel(container_frame, text="ISBN:", font=self.label_font).grid(row=1, column=0, sticky='w', padx=(10,5), pady=8)
        self.isbn_entry = ctk.CTkEntry(container_frame, font=self.entry_font, width=200, corner_radius=6, placeholder_text="Enter 10 or 13 digits")
        self.isbn_entry.grid(row=1, column=1, sticky='w', padx=5, pady=8) # Use sticky 'w'
        fetch_btn = ctk.CTkButton(container_frame, text="Fetch Details",
                                  command=self._fetch_book_details_from_api,
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  width=100, height=30, corner_radius=6)
        fetch_btn.grid(row=1, column=2, padx=(5, 10), pady=8)

        # --- Book Cover Placeholder ---
        # Place it starting from row 1, spanning several rows in column 3
        self.cover_label = ctk.CTkLabel(container_frame, text="Cover Preview", # Placeholder text
                                       font=ctk.CTkFont(size=10),
                                       width=140, height=200, # Approximate size
                                       fg_color=("gray75", "gray25"), # Placeholder bg
                                       corner_radius=6)
        self.cover_label.grid(row=1, column=3, rowspan=6, padx=(10, 10), pady=8, sticky='ns') # Span rows 1 to 6

        # --- Other Fields (Adjust grid column span) ---
        labels = ["Book ID (Optional):", "Book Name:", "Author(s):", "Edition (Publisher, Year):", "Price:", "Quantity:"]
        entries = []
        entry_opts = {'font': self.entry_font, 'corner_radius': 6} # Width determined by grid weight now
        label_opts = {'font': self.label_font}

        for i, label_text in enumerate(labels):
            ctk.CTkLabel(container_frame, text=label_text, **label_opts).grid(row=i+2, column=0, sticky='w', padx=(10,5), pady=8)
            entry = ctk.CTkEntry(container_frame, **entry_opts)
            # Span columns 1 and 2 (middle columns)
            entry.grid(row=i+2, column=1, columnspan=2, sticky='ew', padx=5, pady=8)
            entries.append(entry)

        (self.id_entry, self.bookname_entry, self.author_entry,
         self.edition_entry, self.price_entry, self.qty_entry) = entries

        # --- Submit Button (Adjust grid column span) ---
        submit_btn = ctk.CTkButton(container_frame, text='Submit Book', font=self.button_font,
                                  command=self.SubmitAddBook,
                                  width=150, height=35, corner_radius=8,
                                  fg_color="green", hover_color="#006400")
        # Place below entries, span middle columns
        submit_btn.grid(row=len(labels)+2, column=1, columnspan=2, pady=(25, 15), sticky="ew")

        self.isbn_entry.focus()
        self.UpdateStatusBar("Enter ISBN and click 'Fetch Details' or fill manually.")

    # Add a helper method to clear the cover image
    def _clear_cover_image(self):
         if hasattr(self, 'cover_label'):
              # Reset the cover label to its initial state
              self.cover_label.configure(image=None, text="Cover Preview")

    # Modify ClearScreen to also clear the cover
    def ClearScreen(self):
        """Removes widgets from frame_1 and frame_3, resets status bar and cover."""
        for widget in self.frame_1.winfo_children():
            widget.destroy()
        for widget in self.frame_3.winfo_children():
            widget.destroy()
        # Clear cover specifically if it exists
        if hasattr(self, 'cover_label') and self.cover_label.winfo_exists():
             self._clear_cover_image()
        self.UpdateStatusBar("Ready.")
    


    def SubmitAddBook(self):
        """Handles the submission of the new book form."""
        book_id = self.id_entry.get().strip()
        book_name = self.bookname_entry.get().strip()
        author = self.author_entry.get().strip()
        edition = self.edition_entry.get().strip()
        price_str = self.price_entry.get().strip()
        qty_str = self.qty_entry.get().strip()

        # Validation
        if not all([book_id, book_name]): # Require at least Book ID and Name
            messagebox.showerror("Input Error", "Book ID and Book Name are required.", parent=self.window)
            return
        # Validate Price (optional, allow empty or zero)
        try:
             price = float(price_str) if price_str else 0.0
             if price < 0: raise ValueError("Price cannot be negative.")
        except ValueError as e:
             messagebox.showerror("Input Error", f"Invalid input for Price: {e}", parent=self.window)
             return
        # Validate Quantity (required, must be integer >= 0)
        try:
             qty = int(qty_str) if qty_str else 0 # Default to 0 if empty? Or require it? Let's require > 0
             if not qty_str or qty < 0: # Changed logic: require non-empty and >= 0
                  raise ValueError("Quantity must be a whole number (0 or greater).")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input for Quantity: {e}", parent=self.window)
            return

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return

            curs.execute("SELECT book_id FROM book_list WHERE book_id=%s", (book_id,))
            if curs.fetchone():
                messagebox.showerror("Entry Error", f"Book ID '{book_id}' already exists. Please use a unique ID.", parent=self.window)
                return

            sql = "INSERT INTO book_list (book_id, book_name, author, edition, price, qty) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (book_id, book_name, author or None, edition or None, price, qty) # Handle empty author/edition
            curs.execute(sql, values)
            connection.commit()

            messagebox.showinfo("Success", f"Book '{book_name}' added successfully!", parent=self.window)
            self.UpdateStatusBar(f"Book ID {book_id} added.")
            self.reset_add_book_fields()

        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to add book.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error adding book ID {book_id}.")
            if connection: connection.rollback()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error adding book ID {book_id}.")
        finally:
            self._close_db(connection)


    # --- Show All Books ---
    def ShowBooks(self):
        """Displays all books from the database in a styled Treeview."""
        self.ClearScreen()
        self.UpdateStatusBar("Loading all books...")
        ctk.CTkLabel(self.frame_1, text="Available Books", font=self.heading_font).pack(pady=(10, 5))

        columns_config = [
            ('book_id', 'Book ID', 100, 'w'), ('book_name', 'Book Name', 250, 'w'),
            ('author', 'Author', 200, 'w'), ('edition', 'Edition', 100, 'w'), # Wider Edition
            ('price', 'Price', 90, 'e'), ('qty', 'Quantity', 80, 'center')
        ]
        self.tree = self._create_treeview(self.frame_1, columns_config, cs.columns)
        self.tree.bind('<Double-Button-1>', self.OnSelectedForBookActions)

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return
            curs.execute("SELECT * FROM book_list ORDER BY book_name")
            rows = curs.fetchall()

            if not rows:
                self.UpdateStatusBar("No books found in the database.")
                ctk.CTkLabel(self.tree.master, text="No books available.").pack(pady=20) # Use tree's parent
            else:
                for row in rows:
                    formatted_row = list(row)
                    try:
                        # Format price if it's a number-like value
                        price_val = formatted_row[4]
                        if isinstance(price_val, (int, float)) or (isinstance(price_val, str) and price_val.replace('.', '', 1).isdigit()):
                            formatted_row[4] = f"{float(price_val):.2f}"
                        elif price_val is None:
                             formatted_row[4] = "0.00" # Or N/A
                        else: # Keep original string if not easily convertible
                            formatted_row[4] = str(price_val) if price_val is not None else "N/A"
                    except (ValueError, TypeError):
                        formatted_row[4] = "Error"
                    self.tree.insert("", 'end', values=formatted_row)
                self.UpdateStatusBar(f"Displayed {len(rows)} books.")

        except pymysql.Error as e:
             messagebox.showerror("Database Error", f"Failed to fetch books.\nError: {e}", parent=self.window)
             self.UpdateStatusBar("Error loading books.")
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar("Error loading books.")
        finally:
            self._close_db(connection)

    # --- Book Actions (Delete/Update) ---
    def OnSelectedForBookActions(self, event):
        """Handles double-click on the book list, showing CTk context buttons."""
        selected_item = self.tree.focus()
        if not selected_item: return
        for widget in self.frame_3.winfo_children(): widget.destroy()

        btn_opts = {'font': self.button_font, 'corner_radius': 6, 'height': 30, 'width': 90}
        grid_opts = {'pady': 2, 'padx': 10, 'sticky': 'ew'}
        del_btn = ctk.CTkButton(self.frame_3, text='Delete', command=self.DeleteBook, fg_color="red", hover_color="#B22222", **btn_opts)
        del_btn.grid(row=0, column=0, **grid_opts)
        upd_btn = ctk.CTkButton(self.frame_3, text='Update', command=self.UpdateBookDetailsForm, fg_color="orange", hover_color="#FF8C00", **btn_opts)
        upd_btn.grid(row=0, column=1, **grid_opts)
        self.UpdateStatusBar("Select 'Delete' or 'Update' for the selected book.")

    def DeleteBook(self):
        """Deletes the book selected in the treeview."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showerror("Selection Error", "Please select a book record to delete.", parent=self.window)
            return

        row_values = self.tree.item(selected_item)['values']
        book_id_to_delete = row_values[0]
        book_name = row_values[1]

        if not messagebox.askyesno('Confirm Delete', f"Delete '{book_name}' (ID: {book_id_to_delete})?\nThis action cannot be undone.", icon='warning', parent=self.window):
            return

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return

            curs.execute("SELECT COUNT(*) FROM borrow_record WHERE book_id=%s", (book_id_to_delete,))
            borrow_count = curs.fetchone()[0]
            if borrow_count > 0:
                messagebox.showwarning("Action Denied", f"Cannot delete '{book_name}'. It is currently borrowed by {borrow_count} student(s).", parent=self.window)
                self.UpdateStatusBar(f"Deletion denied for Book ID {book_id_to_delete} (borrowed).")
                return

            curs.execute("DELETE FROM book_list WHERE book_id=%s", (book_id_to_delete,))
            connection.commit()
            messagebox.showinfo("Success", f"Book '{book_name}' deleted successfully.", parent=self.window)
            self.UpdateStatusBar(f"Book ID {book_id_to_delete} deleted.")
            self.ShowBooks() # Refresh the view

        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete book.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error deleting book ID {book_id_to_delete}.")
            if connection: connection.rollback()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error deleting book ID {book_id_to_delete}.")
        finally:
            self._close_db(connection)

    def UpdateBookDetailsForm(self):
        """Displays the form to update details using CTk widgets."""
        selected_item = self.tree.focus()
        if not selected_item:
             messagebox.showerror("Selection Error", "Please select a book record to update.", parent=self.window)
             return
        row_values = self.tree.item(selected_item)['values']

        self.ClearScreen()
        self.UpdateStatusBar(f"Update details for Book ID: {row_values[0]}")

        form_frame = ctk.CTkFrame(self.frame_1, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, anchor='n')
        ctk.CTkLabel(form_frame, text="Update Book Details", font=self.heading_font).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Display Book ID
        ctk.CTkLabel(form_frame, text="Book ID:", font=self.label_font).grid(row=1, column=0, sticky='w', padx=5, pady=8)
        # Use a disabled entry or a label to show non-editable ID
        ctk.CTkLabel(form_frame, text=row_values[0], font=self.entry_font, width=290, anchor='w', justify='left').grid(row=1, column=1, sticky='ew', padx=5, pady=8)

        # Editable fields
        labels = ["Book Name:", "Author:", "Edition:", "Price:", "Quantity:"]
        current_values = row_values[1:]
        entries = []
        entry_opts = {'font': self.entry_font, 'width': 300, 'corner_radius': 6}
        label_opts = {'font': self.label_font}
        for i, label_text in enumerate(labels):
            ctk.CTkLabel(form_frame, text=label_text, **label_opts).grid(row=i+2, column=0, sticky='w', padx=5, pady=8)
            entry = ctk.CTkEntry(form_frame, **entry_opts)
            entry.grid(row=i+2, column=1, sticky='ew', padx=5, pady=8)
            entry.insert(0, current_values[i] if current_values[i] is not None else "") # Handle potential None values
            entries.append(entry)

        # Assign to specific attributes for SubmitUpdateBook
        (self.update_bookname_entry, self.update_author_entry,
         self.update_edition_entry, self.update_price_entry, self.update_qty_entry) = entries

        submit_command = partial(self.SubmitUpdateBook, row_values[0]) # Pass Book ID
        submit_btn = ctk.CTkButton(form_frame, text='Submit Update', font=self.button_font, command=submit_command, width=150, height=35, corner_radius=8, fg_color="green", hover_color="#006400")
        submit_btn.grid(row=len(labels)+2, column=0, columnspan=2, pady=(25, 10))

    def SubmitUpdateBook(self, book_id):
        """Handles the submission of updated book details."""
        book_name = self.update_bookname_entry.get().strip()
        author = self.update_author_entry.get().strip()
        edition = self.update_edition_entry.get().strip()
        price_str = self.update_price_entry.get().strip()
        qty_str = self.update_qty_entry.get().strip()

        # Validation (similar to Add Book, require name, validate price/qty)
        if not book_name:
            messagebox.showerror("Input Error", "Book Name is required.", parent=self.window)
            return
        try:
             price = float(price_str) if price_str else 0.0
             if price < 0: raise ValueError("Price cannot be negative.")
        except ValueError as e:
             messagebox.showerror("Input Error", f"Invalid input for Price: {e}", parent=self.window)
             return
        try:
             qty = int(qty_str) if qty_str else 0
             if not qty_str or qty < 0:
                  raise ValueError("Quantity must be a whole number (0 or greater).")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input for Quantity: {e}", parent=self.window)
            return

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return

            sql = """UPDATE book_list SET book_name=%s, author=%s, edition=%s, price=%s, qty=%s
                     WHERE book_id=%s"""
            values = (book_name, author or None, edition or None, price, qty, book_id)
            curs.execute(sql, values)
            connection.commit()

            if curs.rowcount > 0:
                messagebox.showinfo("Success", f"Book ID '{book_id}' updated successfully!", parent=self.window)
                self.UpdateStatusBar(f"Book ID {book_id} updated.")
                self.ShowBooks()
            else:
                 messagebox.showwarning("No Change", f"No changes detected or book ID '{book_id}' not found. Update not performed.", parent=self.window)
                 self.UpdateStatusBar(f"No effective update for Book ID {book_id}.")

        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to update book.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error updating book ID {book_id}.")
            if connection: connection.rollback()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error updating book ID {book_id}.")
        finally:
            self._close_db(connection)

    # --- Issue Book ---
    def GetData_for_IssueBook(self):
        """Displays the form to issue a book using CTk widgets."""
        self.ClearScreen()
        self.UpdateStatusBar("Enter details to issue a book.")

        form_frame = ctk.CTkFrame(self.frame_1, fg_color="transparent")
        form_frame.pack(pady=15, padx=40, anchor='n')
        ctk.CTkLabel(form_frame, text="Issue Book", font=self.heading_font).grid(row=0, column=0, columnspan=3, pady=(0, 20))

        labels = ["Book ID:", "Book Name:", "Student Roll:", "Student Name:", "Course:", "Subject:", "Issue Date:", "Return Date:"]
        entries = []
        entry_opts = {'font': self.entry_font, 'width': 280, 'corner_radius': 6}
        label_opts = {'font': self.label_font}
        for i, label_text in enumerate(labels):
            ctk.CTkLabel(form_frame, text=label_text, **label_opts).grid(row=i+1, column=0, sticky='w', padx=5, pady=6)
            entry = ctk.CTkEntry(form_frame, **entry_opts)
            # Add placeholders for dates
            if "Date" in label_text: entry.configure(placeholder_text="YYYY-MM-DD")
            entry.grid(row=i+1, column=1, sticky='ew', padx=5, pady=6)
            if i == 0: # Book ID row
                 fetch_btn = ctk.CTkButton(form_frame, text="Fetch Name", command=self._fetch_book_name_for_issue, font=ctk.CTkFont(size=10), width=70, height=28, corner_radius=6)
                 fetch_btn.grid(row=i+1, column=2, padx=(5, 0), pady=6)
            entries.append(entry)

        (self.book_id_entry, self.book_name_entry, self.stu_roll_entry, self.stu_name_entry,
         self.course_entry, self.subject_entry, self.issue_date_entry, self.return_date_entry) = entries

        submit_btn = ctk.CTkButton(form_frame, text='Submit Issue', font=self.button_font, command=self.SubmitIssueBook, width=150, height=35, corner_radius=8, fg_color="green", hover_color="#006400")
        submit_btn.grid(row=len(labels)+1, column=0, columnspan=3, pady=(20, 10))
        self.book_id_entry.focus()

    def _fetch_book_name_for_issue(self):
        """Helper to fetch book name based on ID entered in issue form."""
        book_id = self.book_id_entry.get().strip()
        if not book_id:
            self.UpdateStatusBar("Enter a Book ID to fetch its name.")
            return

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return
            curs.execute("SELECT book_name FROM book_list WHERE book_id=%s", (book_id,))
            result = curs.fetchone()

            if result:
                self.book_name_entry.delete(0, ctk.END)
                self.book_name_entry.insert(0, result[0])
                self.UpdateStatusBar(f"Fetched name for Book ID {book_id}.")
            else:
                messagebox.showwarning("Not Found", f"Book ID '{book_id}' not found in library.", parent=self.window)
                self.book_name_entry.delete(0, ctk.END)
                self.UpdateStatusBar(f"Book ID {book_id} not found.")

        except pymysql.Error as e:
             messagebox.showerror("Database Error", f"Error fetching book name: {e}", parent=self.window)
             self.UpdateStatusBar("Error fetching book name.")
        finally:
            self._close_db(connection)

    def SubmitIssueBook(self):
        """Handles the submission of the book issue form."""
        book_id = self.book_id_entry.get().strip()
        book_name = self.book_name_entry.get().strip() # Get potentially fetched name
        stu_roll = self.stu_roll_entry.get().strip()
        stu_name = self.stu_name_entry.get().strip()
        course = self.course_entry.get().strip()
        subject = self.subject_entry.get().strip()
        issue_date = self.issue_date_entry.get().strip()
        return_date = self.return_date_entry.get().strip()

        if not all([book_id, book_name, stu_roll, stu_name, issue_date, return_date]): # Basic check
             messagebox.showerror("Input Error", "All fields are required to issue a book.", parent=self.window)
             return
        # Add date validation here if needed

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return

            # Check Book Availability
            curs.execute("SELECT qty FROM book_list WHERE book_id=%s", (book_id,))
            result = curs.fetchone()
            if not result:
                messagebox.showerror("Book Error", f"Book ID '{book_id}' does not exist in the library.", parent=self.window)
                return
            current_qty = result[0]
            if current_qty < 1:
                messagebox.showwarning("Unavailable", f"Book '{book_name}' (ID: {book_id}) is out of stock.", parent=self.window)
                return

            # Check Student Limit
            curs.execute("SELECT COUNT(*) FROM borrow_record WHERE stu_roll=%s", (stu_roll,))
            borrow_count = curs.fetchone()[0]
            MAX_BORROW_LIMIT = 3
            if borrow_count >= MAX_BORROW_LIMIT:
                 messagebox.showerror("Limit Exceeded", f"Student (Roll: {stu_roll}) already has {MAX_BORROW_LIMIT} books.", parent=self.window)
                 return

            # Check if Student Already Borrowed THIS Book
            curs.execute("SELECT book_id FROM borrow_record WHERE stu_roll=%s AND book_id=%s", (stu_roll, book_id))
            if curs.fetchone():
                messagebox.showerror("Duplicate Issue", f"Student (Roll: {stu_roll}) already has this book (ID: {book_id}).", parent=self.window)
                return

            # --- Proceed with Issue Transaction ---
            sql_insert = """INSERT INTO borrow_record (book_id, book_name, stu_roll, stu_name, course, subject, issue_date, return_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values_insert = (book_id, book_name, stu_roll, stu_name, course or None, subject or None, issue_date, return_date)
            curs.execute(sql_insert, values_insert)

            new_qty = current_qty - 1
            sql_update = "UPDATE book_list SET qty=%s WHERE book_id=%s"
            curs.execute(sql_update, (new_qty, book_id))

            connection.commit() # Commit both changes

            messagebox.showinfo("Success", f"Book '{book_name}' issued to {stu_name} (Roll: {stu_roll}).", parent=self.window)
            self.UpdateStatusBar(f"Book ID {book_id} issued to Roll {stu_roll}.")
            self.reset_issue_book_fields()

        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to issue book.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error issuing book ID {book_id}.")
            if connection: connection.rollback()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error issuing book ID {book_id}.")
             if connection: connection.rollback()
        finally:
            self._close_db(connection)

    # --- Return Book ---
    def ReturnBook(self):
        """Displays form to enter student roll number for returning books."""
        self.ClearScreen()
        self.UpdateStatusBar("Enter student roll number to view borrowed books.")

        input_frame = ctk.CTkFrame(self.frame_1, fg_color="transparent")
        input_frame.pack(pady=40, padx=30, anchor='n')
        ctk.CTkLabel(input_frame, text="Return Book", font=self.heading_font).pack(pady=(0, 25))
        ctk.CTkLabel(input_frame, text="Enter Student Roll No:", font=self.label_font).pack(pady=5)
        self.return_roll_entry = ctk.CTkEntry(input_frame, font=self.entry_font, width=250, height=35, corner_radius=6)
        self.return_roll_entry.pack(pady=10)
        self.return_roll_entry.focus()
        search_btn = ctk.CTkButton(input_frame, text='Search Records', font=self.button_font, command=self.ShowRecordsForReturn, width=150, height=35, corner_radius=8, fg_color="orange", hover_color="#FF8C00")
        search_btn.pack(pady=20)

    def ShowRecordsForReturn(self):
        """Displays borrowed books for return using CTk container and styled Treeview."""
        # Check if return_roll_entry exists before getting value
        if not hasattr(self, 'return_roll_entry'):
             messagebox.showerror("Error", "Roll entry not found. Please go back to Return Book screen.", parent=self.window)
             return # Or call self.ReturnBook() to reset the screen

        stu_roll = self.return_roll_entry.get().strip()
        if not stu_roll:
            messagebox.showerror("Input Error", "Please enter a Student Roll Number.", parent=self.window)
            return

        self.ClearScreen()
        self.UpdateStatusBar(f"Loading borrow records for Roll No: {stu_roll}...")
        ctk.CTkLabel(self.frame_1, text=f"Books Borrowed by Roll No: {stu_roll}", font=self.heading_font).pack(pady=(10, 5))

        columns_config = [
            ('book_id', 'Book ID', 100, 'w'), ('book_name', 'Book Name', 220, 'w'),
            ('student_name', 'Student Name', 150, 'w'),
            ('issue_date', 'Issue Date', 110, 'center'), ('return_date', 'Return Date', 110, 'center')
        ]
        data_columns = cs.columns_1 # Use tuple from customs
        self.tree_1 = self._create_treeview(self.frame_1, columns_config, data_columns)
        # Ensure displaycolumns matches columns_config IDs if needed, but showing all from data_columns is fine
        self.tree_1['displaycolumns'] = ('book_id', 'book_name', 'student_name', 'issue_date', 'return_date')
        self.current_return_roll = stu_roll
        self.tree_1.bind('<Double-Button-1>', self.OnSelectedForReturnActions)

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return
            curs.execute("SELECT * FROM borrow_record WHERE stu_roll=%s", (stu_roll,))
            rows = curs.fetchall()

            if not rows:
                self.UpdateStatusBar(f"No active borrow records found for Roll No: {stu_roll}.")
                messagebox.showinfo("No Records", f"No books currently borrowed by Roll No: {stu_roll}.", parent=self.window)
                self.ReturnBook() # Go back to input screen
            else:
                for row in rows: self.tree_1.insert("", 'end', values=row)
                self.UpdateStatusBar(f"Displayed {len(rows)} books for Roll No: {stu_roll}. Double-click for actions.")
        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch borrow records.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error loading records for {stu_roll}.")
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error loading records for {stu_roll}.")
        finally:
            self._close_db(connection)

    def OnSelectedForReturnActions(self, event):
        """Handles double-click on return list, showing CTk context buttons."""
        # Ensure tree_1 exists before proceeding
        if not hasattr(self, 'tree_1') or not self.tree_1.winfo_exists(): return
        selected_item = self.tree_1.focus()
        if not selected_item: return
        for widget in self.frame_3.winfo_children(): widget.destroy()

        btn_opts = {'font': self.button_font, 'corner_radius': 6, 'height': 30, 'width': 90}
        grid_opts = {'pady': 2, 'padx': 10, 'sticky': 'ew'}
        return_btn = ctk.CTkButton(self.frame_3, text='Return', command=self.PerformReturnBook, fg_color="green", hover_color="#006400", **btn_opts)
        return_btn.grid(row=0, column=0, **grid_opts)
        reissue_btn = ctk.CTkButton(self.frame_3, text='Re-Issue', command=self.ReIssueBookForm, fg_color="orange", hover_color="#FF8C00", **btn_opts)
        reissue_btn.grid(row=0, column=1, **grid_opts)
        self.UpdateStatusBar("Select 'Return' or 'Re-Issue' for the selected record.")

    def PerformReturnBook(self):
        """Processes the return of the selected book."""
        if not hasattr(self, 'tree_1') or not self.tree_1.winfo_exists(): return # Safety check
        selected_item = self.tree_1.focus()
        if not selected_item:
            messagebox.showerror("Selection Error", "Please select a record to return.", parent=self.window)
            return

        row_values = self.tree_1.item(selected_item)['values']
        book_id, book_name, stu_roll = row_values[0], row_values[1], row_values[2]

        if not messagebox.askyesno('Confirm Return', f"Return: {book_name} (ID: {book_id})\nFrom Roll: {stu_roll}?", parent=self.window):
            return

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return

            # --- Return Transaction ---
            sql_delete = "DELETE FROM borrow_record WHERE stu_roll=%s AND book_id=%s"
            deleted_count = curs.execute(sql_delete, (stu_roll, book_id))

            if deleted_count > 0:
                sql_update = "UPDATE book_list SET qty = qty + 1 WHERE book_id=%s"
                curs.execute(sql_update, (book_id,))
                connection.commit() # Commit both changes
                messagebox.showinfo("Success", f"Book '{book_name}' returned successfully.", parent=self.window)
                self.UpdateStatusBar(f"Book ID {book_id} returned from Roll {stu_roll}.")
                # Refresh list for the same student
                # Need to check if return_roll_entry still exists or get roll from stored attr
                current_roll = getattr(self, 'current_return_roll', None)
                if current_roll:
                     # Simulate entering roll again if entry doesn't exist
                     if not hasattr(self, 'return_roll_entry') or not self.return_roll_entry.winfo_exists():
                          self.ReturnBook() # Go back to input screen first
                          self.return_roll_entry.insert(0, current_roll) # Insert roll
                     self.ShowRecordsForReturn() # Then show records
                else:
                     self.ReturnBook() # Fallback to main return screen
            else:
                 messagebox.showerror("Error", "Could not find the borrow record. Maybe returned already?", parent=self.window)
                 if connection: connection.rollback()

        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to return book.\nError: {e}", parent=self.window)
            self.UpdateStatusBar(f"Error returning book ID {book_id} for {stu_roll}.")
            if connection: connection.rollback()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error returning book ID {book_id} for {stu_roll}.")
             if connection: connection.rollback()
        finally:
            self._close_db(connection)

    def ReIssueBookForm(self):
        """Displays form to update return date using CTk widgets."""
        if not hasattr(self, 'tree_1') or not self.tree_1.winfo_exists(): return
        selected_item = self.tree_1.focus()
        if not selected_item:
             messagebox.showerror("Selection Error", "Please select a record to re-issue.", parent=self.window)
             return
        row_values = self.tree_1.item(selected_item)['values']

        self.ClearScreen()
        self.UpdateStatusBar(f"Re-issuing Book ID {row_values[0]} to Roll {row_values[2]}.")

        form_frame = ctk.CTkFrame(self.frame_1, fg_color="transparent")
        form_frame.pack(pady=15, padx=40, anchor='n')
        ctk.CTkLabel(form_frame, text="Re-Issue Book", font=self.heading_font).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        details = [
            ("Book ID:", row_values[0]), ("Book Name:", row_values[1]),
            ("Student Roll:", row_values[2]), ("Student Name:", row_values[3]),
            ("Issue Date:", row_values[6]), ("Current Return:", row_values[7])
        ]
        for i, (label_text, value_text) in enumerate(details):
            ctk.CTkLabel(form_frame, text=label_text, font=self.label_font).grid(row=i+1, column=0, sticky='w', padx=5, pady=6)
            ctk.CTkLabel(form_frame, text=value_text or "N/A", font=self.entry_font, width=290, anchor='w', justify='left').grid(row=i+1, column=1, sticky='ew', padx=5, pady=6)

        ctk.CTkLabel(form_frame, text="New Return Date:", font=self.label_font).grid(row=len(details)+1, column=0, sticky='w', padx=5, pady=8)
        self.new_return_date_entry = ctk.CTkEntry(form_frame, font=self.entry_font, width=300, corner_radius=6, placeholder_text="YYYY-MM-DD")
        self.new_return_date_entry.grid(row=len(details)+1, column=1, sticky='ew', padx=5, pady=8)
        self.new_return_date_entry.focus()

        submit_command = partial(self.SubmitReIssue, row_values[0], row_values[2])
        submit_btn = ctk.CTkButton(form_frame, text='Submit Re-Issue', font=self.button_font, command=submit_command, width=150, height=35, corner_radius=8, fg_color="green", hover_color="#006400")
        submit_btn.grid(row=len(details)+2, column=0, columnspan=2, pady=(20, 10))

    def SubmitReIssue(self, book_id, stu_roll):
         """Updates the return date in the borrow_record table."""
         new_return_date = self.new_return_date_entry.get().strip()
         if not new_return_date: # Add date format validation if desired
             messagebox.showerror("Input Error", "Please enter the new return date (YYYY-MM-DD).", parent=self.window)
             return

         connection, curs = None, None
         try:
             connection, curs = self._connect_db()
             if not connection: return

             sql = "UPDATE borrow_record SET return_date=%s WHERE book_id=%s AND stu_roll=%s"
             updated_count = curs.execute(sql, (new_return_date, book_id, stu_roll))
             connection.commit()

             if updated_count > 0:
                 messagebox.showinfo("Success", f"Return date updated successfully.", parent=self.window)
                 self.UpdateStatusBar(f"Book ID {book_id} re-issued to {stu_roll} until {new_return_date}.")
                 # Refresh list for the same student
                 current_roll = getattr(self, 'current_return_roll', None)
                 if current_roll:
                      if not hasattr(self, 'return_roll_entry') or not self.return_roll_entry.winfo_exists():
                           self.ReturnBook()
                           self.return_roll_entry.insert(0, current_roll)
                      self.ShowRecordsForReturn()
                 else:
                      self.ReturnBook()
             else:
                 messagebox.showerror("Error", "Could not update the record. Maybe returned already?", parent=self.window)
                 self.UpdateStatusBar(f"Failed to re-issue Book ID {book_id} for {stu_roll}.")

         except pymysql.Error as e:
             messagebox.showerror("Database Error", f"Failed to update return date.\nError: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error re-issuing Book ID {book_id} for {stu_roll}.")
             if connection: connection.rollback()
         except Exception as e:
              messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
              self.UpdateStatusBar(f"Error re-issuing Book ID {book_id} for {stu_roll}.")
         finally:
             self._close_db(connection)

    # --- Search Book ---
    def GetBookNametoSearch(self):
        """Displays search input form using CTk widgets."""
        self.ClearScreen()
        self.UpdateStatusBar("Enter book name (or part of it) to search.")

        input_frame = ctk.CTkFrame(self.frame_1, fg_color="transparent")
        input_frame.pack(pady=40, padx=30, anchor='n')
        ctk.CTkLabel(input_frame, text="Search Book", font=self.heading_font).pack(pady=(0, 25))
        ctk.CTkLabel(input_frame, text="Enter Book Name:", font=self.label_font).pack(pady=5)
        self.search_book_entry = ctk.CTkEntry(input_frame, font=self.entry_font, width=300, height=35, corner_radius=6, placeholder_text="Enter keyword...")
        self.search_book_entry.pack(pady=10)
        self.search_book_entry.focus()
        search_btn = ctk.CTkButton(input_frame, text='Search', font=self.button_font, command=self.PerformSearchBook, width=150, height=35, corner_radius=8, fg_color="orange", hover_color="#FF8C00")
        search_btn.pack(pady=20)

    def PerformSearchBook(self):
        """Performs search and displays results in styled Treeview."""
        search_term = self.search_book_entry.get().strip()
        if not search_term:
            messagebox.showerror("Input Error", "Please enter a book name or keyword.", parent=self.window)
            return

        self.ClearScreen()
        self.UpdateStatusBar(f"Searching for books like '{search_term}'...")
        ctk.CTkLabel(self.frame_1, text=f"Search Results for: '{search_term}'", font=self.heading_font).pack(pady=(10, 5))

        columns_config = [
            ('book_id', 'Book ID', 100, 'w'), ('book_name', 'Book Name', 250, 'w'),
            ('author', 'Author', 200, 'w'), ('edition', 'Edition', 100, 'w'),
            ('price', 'Price', 90, 'e'), ('qty', 'Quantity', 80, 'center')
        ]
        self.tree = self._create_treeview(self.frame_1, columns_config, cs.columns)
        self.tree.bind('<Double-Button-1>', self.OnSelectedForBookActions)

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return
            search_pattern = f"%{search_term}%"
            curs.execute("SELECT * FROM book_list WHERE book_name LIKE %s ORDER BY book_name", (search_pattern,))
            rows = curs.fetchall()

            if not rows:
                self.UpdateStatusBar(f"No books found matching '{search_term}'.")
                messagebox.showinfo("No Results", f"No books found matching '{search_term}'.", parent=self.window)
                self.GetBookNametoSearch() # Go back to search input
            else:
                for row in rows:
                     formatted_row = list(row)
                     try:
                         price_val = formatted_row[4]
                         if isinstance(price_val, (int, float)) or (isinstance(price_val, str) and price_val.replace('.', '', 1).isdigit()):
                             formatted_row[4] = f"{float(price_val):.2f}"
                         elif price_val is None: formatted_row[4] = "0.00"
                         else: formatted_row[4] = str(price_val) if price_val is not None else "N/A"
                     except (ValueError, TypeError): formatted_row[4] = "Error"
                     self.tree.insert("", 'end', values=formatted_row)
                self.UpdateStatusBar(f"Found {len(rows)} book(s). Double-click for actions.")
        except pymysql.Error as e:
             messagebox.showerror("Database Error", f"Failed to search books.\nError: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error searching for '{search_term}'.")
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
             self.UpdateStatusBar(f"Error searching for '{search_term}'.")
        finally:
            self._close_db(connection)

    # --- Book Holders ---
    def AllBorrowRecords(self):
        """Displays all borrow records using styled Treeview."""
        self.ClearScreen()
        self.UpdateStatusBar("Loading all borrow records...")
        ctk.CTkLabel(self.frame_1, text="Current Book Holders", font=self.heading_font).pack(pady=(10, 5))

        columns_config = [
            ('book_id', 'Book ID', 100, 'w'), ('book_name', 'Book Name', 180, 'w'),
            ('student_roll', 'Roll No', 100, 'w'), ('student_name', 'Student Name', 150, 'w'),
            ('issue_date', 'Issue Date', 110, 'center'), ('return_date', 'Return Date', 110, 'center')
        ]
        data_columns = cs.columns_1 # Use tuple from customs

        self.tree_1 = self._create_treeview(self.frame_1, columns_config, data_columns)
        # Display only relevant columns
        self.tree_1['displaycolumns'] = ('book_id', 'book_name', 'student_roll', 'student_name', 'issue_date', 'return_date')
        # Optionally bind double-click to return/re-issue actions
        # self.tree_1.bind('<Double-Button-1>', self.OnSelectedForReturnActions)

        connection, curs = None, None
        try:
            connection, curs = self._connect_db()
            if not connection: return
            curs.execute("SELECT * FROM borrow_record ORDER BY stu_roll, issue_date")
            rows = curs.fetchall()

            if not rows:
                self.UpdateStatusBar("No books are currently borrowed.")
                messagebox.showinfo("No Records", "No books are currently issued to students.", parent=self.window)
            else:
                for row in rows: self.tree_1.insert("", 'end', values=row)
                self.UpdateStatusBar(f"Displayed {len(rows)} active borrow records.")
        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch borrow records.\nError: {e}", parent=self.window)
            self.UpdateStatusBar("Error loading borrow records.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
            self.UpdateStatusBar("Error loading borrow records.")
        finally:
            self._close_db(connection)

    # --- Exit ---
    def Exit(self):
        """Shows a confirmation dialog and exits the application."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?", icon='question', parent=self.window):
            self.window.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = ctk.CTk()
    app = Management(root)
    root.mainloop()

# --- END OF main.py (Corrected Version with API Fetch) ---