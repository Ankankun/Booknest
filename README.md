# Library Management System (CustomTkinter GUI + API)

A modern, user-friendly desktop application for managing a library's book inventory and borrowing records. Built with Python, it features a clean graphical user interface using CustomTkinter, connects to a MySQL database for data persistence, and integrates with the Open Library API to automatically fetch book details via ISBN.

![Screenshot Placeholder](<Screenshot URL or Path - Replace this!>)
*(Replace the line above with an actual screenshot of your application)*

## Features

*   **Modern UI:** Clean and themeable interface using the CustomTkinter library.
*   **Book Management:**
    *   **Add Books:** Manually enter book details or fetch automatically using ISBN via Open Library API.
    *   **View All Books:** Display the entire library catalog in a sortable table.
    *   **Search Books:** Find books by name (keyword search).
    *   **Update Books:** Modify details of existing books.
    *   **Delete Books:** Remove books from the catalog (only if not currently borrowed).
*   **Borrowing Management:**
    *   **Issue Books:** Record books borrowed by students (with validation for availability and borrow limits).
    *   **Return Books:** Process book returns, updating inventory quantity.
    *   **Re-Issue Books:** Extend the borrowing period by updating the return date.
    *   **View Book Holders:** See a list of all books currently on loan and who borrowed them.
*   **Database Integration:** Uses MySQL for reliable data storage.
*   **API Integration:** Fetches book title, author, and edition details automatically from the [Open Library Books API](https://openlibrary.org/dev/docs/api/books) using the ISBN.

## Technologies Used

*   **Python 3.x**
*   **CustomTkinter:** For the modern graphical user interface.
*   **Pillow (PIL Fork):** For handling images (if implementing cover display).
*   **Requests:** For making API calls to Open Library.
*   **pymysql:** For connecting to and interacting with the MySQL database.
*   **MySQL:** Relational database for storing book and borrower information.
*   **Open Library Books API:** External API for fetching book metadata.

## Setup and Installation

Follow these steps to get the application running on your local machine:

1.  **Prerequisites:**
    *   Python 3.7+ installed ([python.org](https://www.python.org/downloads/)).
    *   MySQL Server installed and running ([mysql.com](https://dev.mysql.com/downloads/mysql/)). You'll need a MySQL client (like MySQL Workbench, DBeaver, or command line) to set up the database initially.

2.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory-name>
    ```

3.  **Install Dependencies:**
    Create and activate a virtual environment (recommended):
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
    Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` doesn't exist, create it with `pip freeze > requirements.txt` after installing: `pip install customtkinter pillow requests pymysql`)*

4.  **Database Setup:**
    *   Connect to your MySQL server using your client.
    *   Create the database (adjust the name if different from `credentials.py`):
        ```sql
        CREATE DATABASE IF NOT EXISTS library_management;
        USE library_management;
        ```
    *   Create the necessary tables:
        ```sql
        -- Table for storing book details
        CREATE TABLE IF NOT EXISTS book_list (
            book_id VARCHAR(50) PRIMARY KEY,  -- Unique identifier (often ISBN)
            book_name VARCHAR(255) NOT NULL, -- Title of the book
            author VARCHAR(512),             -- Author(s)
            edition VARCHAR(255),            -- Edition info (e.g., Publisher, Year)
            price DECIMAL(10, 2) DEFAULT 0.00, -- Price
            qty INT DEFAULT 0                -- Quantity currently in stock
        );

        -- Table for tracking borrowed books
        CREATE TABLE IF NOT EXISTS borrow_record (
            borrow_id INT AUTO_INCREMENT PRIMARY KEY, -- Optional auto-incrementing ID
            book_id VARCHAR(50),             -- FK reference to book_list
            book_name VARCHAR(255),          -- Denormalized for easy display
            stu_roll VARCHAR(50) NOT NULL,   -- Student's roll number
            stu_name VARCHAR(255),           -- Student's name
            course VARCHAR(100),             -- Student's course
            subject VARCHAR(100),            -- Subject related
            issue_date VARCHAR(20),          -- Issue date (consider DATE type)
            return_date VARCHAR(20),         -- Due date (consider DATE type)
            -- Optional constraint to prevent duplicate borrows of the same book ID by the same student
            UNIQUE KEY unique_borrow (book_id, stu_roll),
            FOREIGN KEY (book_id) REFERENCES book_list(book_id) ON DELETE RESTRICT ON UPDATE CASCADE
        );
        ```
        *Note: The `borrow_id` and `UNIQUE KEY` in `borrow_record` are optional enhancements.*

5.  **Configure Credentials:**
    *   Open the `credentials.py` file.
    *   Replace the placeholder values with your actual MySQL connection details:
        *   `host`: Usually `'localhost'` if the database is on the same machine.
        *   `user`: Your MySQL username (e.g., `'root'`).
        *   `password`: Your MySQL password.
        *   `database`: The name of the database you created (e.g., `'library_management'`).
    *   **Important:** Add `credentials.py` to your `.gitignore` file to avoid accidentally committing sensitive information.

## Usage

1.  Ensure your MySQL server is running.
2.  Activate your virtual environment (if you created one).
3.  Run the main application file from the project's root directory:
    ```bash
    python main.py
    ```
4.  Use the buttons in the right panel to navigate through different functionalities (Add Book, View All Books, Issue Book, etc.).

## API Integration

*   The "Add Book" feature uses the **Open Library Books API**.
*   When you enter a valid 10 or 13-digit ISBN and click "Fetch Details", the application queries the API.
*   If found, it automatically populates the Book Name, Author(s), and Edition fields.
*   The ISBN is typically used as the default Book ID.
*   No API key is required for this basic Open Library functionality.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*(Optional Sections)*

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

## Future Enhancements

*   Implement book cover display using API data.
*   Add a dashboard with library statistics.
*   Highlight overdue books in lists.
*   Integrate a calendar widget for date selection.
*   Implement basic user roles (admin/librarian).
*   Improve search functionality (e.g., search by author, advanced filters).
*   Use proper `DATE` types in the database for better date handling.
