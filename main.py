import os
import re
import pdfplumber
from transformers import pipeline
import tkinter as tk
from tkinter import filedialog, messagebox
from pymongo import MongoClient

# Medical summarization functions
def load_medical_records(file_path):
    """Load medical records from a PDF file."""
    if os.path.exists(file_path):
        try:
            with pdfplumber.open(file_path) as pdf:
                records = "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            return records.split('\n\n')
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return []
    else:
        print(f"File not found: {file_path}")
        return []


def extract_vital_signs(text):
    """Extract vital signs like Blood Pressure, Heart Rate, Respiratory Rate, and Temperature."""
    patterns = {
        "Blood Pressure": r"(?:BP|Blood Pressure|B\.P\.):?\s*(\d{2,3}/\d{2,3})",
        "Heart Rate": r"(?:HR|Heart Rate|Pulse):?\s*(\d{2,3})",
        "Respiratory Rate": r"(?:RR|Respiratory Rate):?\s*(\d{1,2})",
        "Temperature": r"(?:Temp|Temperature):?\s*(\d{2}(?:\.\d)?)\s*(?:\u00b0?C|\u00b0?F)?"
    }
    vitals = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        vitals[key] = match.group(1) if match else "Not Found"
    return vitals


def summarize_medical_records(records, summarizer):
    """Summarize medical records using transformers summarization pipeline."""
    summaries = []
    for record in records:
        try:
            if len(record.split()) > 20:  # Skip short paragraphs
                summary = summarizer(record, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            else:
                summary = record
            summaries.append(summary)
        except Exception as e:
            summaries.append(f"Error summarizing record: {e}")
    return summaries


# MongoDB connection
def get_mongo_connection():
    """Establish and return a MongoDB connection."""
    try:
        client = MongoClient("mongodb://localhost:27017/")  # Replace with your connection string
        db = client["medical_app"]  # Database name
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


# GUI Application
class MedicalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Summarization App")
        self.root.state('zoomed')  # Start in full-screen mode
        self.root.configure(bg="#2c3e50")

        # Dictionary to store user credentials
        self.db = get_mongo_connection()
        self.users_collection = self.db["users"] if self.db is not None else None  # Collection to store user data

        self.init_login_page()

    def clear_window(self):
        """Clear all widgets in the current window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_centered_frame(self, bg_color):
        frame = tk.Frame(self.root, bg=bg_color)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        return frame

    def init_login_page(self):
        self.clear_window()

        self.login_frame = self.create_centered_frame("#34495e")
        tk.Label(self.login_frame, text="Login", font=("Arial", 32, "bold"), bg="#34495e", fg="white").pack(pady=20)

        tk.Label(self.login_frame, text="Username", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 18), width=25)
        self.username_entry.pack(pady=10)

        tk.Label(self.login_frame, text="Password", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.password_entry = tk.Entry(self.login_frame, font=("Arial", 18), show="*", width=25)
        self.password_entry.pack(pady=10)

        tk.Button(self.login_frame, text="Login", font=("Arial", 18, "bold"), command=self.validate_login, bg="#2ecc71", fg="white", width=15).pack(pady=10)
        tk.Button(self.login_frame, text="Register", font=("Arial", 18, "bold"), command=self.init_register_page, bg="#e74c3c", fg="white", width=15).pack(pady=10)

    def init_register_page(self):
        self.clear_window()

        self.register_frame = self.create_centered_frame("#34495e")
        tk.Label(self.register_frame, text="Register", font=("Arial", 32, "bold"), bg="#34495e", fg="white").pack(pady=20)

        tk.Label(self.register_frame, text="Username", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.new_username_entry = tk.Entry(self.register_frame, font=("Arial", 18), width=25)
        self.new_username_entry.pack(pady=10)

        tk.Label(self.register_frame, text="Password", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.new_password_entry = tk.Entry(self.register_frame, font=("Arial", 18), show="*", width=25)
        self.new_password_entry.pack(pady=10)

        tk.Button(self.register_frame, text="Register", font=("Arial", 18, "bold"), command=self.register_user, bg="#2ecc71", fg="white", width=15).pack(pady=10)
        tk.Button(self.register_frame, text="Back to Login", font=("Arial", 18, "bold"), command=self.init_login_page, bg="#e74c3c", fg="white", width=15).pack(pady=10)

    def init_dashboard_page(self):
        self.clear_window()

        self.dashboard_frame = tk.Frame(self.root, bg="#2c3e50")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(self.dashboard_frame, bg="#1abc9c", height=100)
        header_frame.pack(fill=tk.BOTH, pady=20)
        tk.Label(header_frame, text="AI Summarization Medical Report", font=("Arial", 32, "bold"), bg="#1abc9c", fg="white").pack(pady=20)

        buttons_frame = tk.Frame(self.dashboard_frame, bg="#2c3e50")
        buttons_frame.pack(expand=True)

        tk.Button(buttons_frame, text="Upload File", font=("Arial", 18, "bold"), command=self.upload_file, bg="#9b59b6", fg="white", width=20).pack(pady=10)
        tk.Button(buttons_frame, text="Profile", font=("Arial", 18, "bold"), command=self.init_profile_page, bg="#3498db", fg="white", width=20).pack(pady=10)
        tk.Button(buttons_frame, text="Logout", font=("Arial", 18, "bold"), command=self.init_login_page, bg="#e74c3c", fg="white", width=20).pack(pady=10)

    def init_profile_page(self):
        self.clear_window()

        self.profile_frame = self.create_centered_frame("#34495e")
        tk.Label(self.profile_frame, text="Profile", font=("Arial", 32, "bold"), bg="#34495e", fg="white").pack(pady=20)

        tk.Label(self.profile_frame, text="Username", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.username_entry_profile = tk.Entry(self.profile_frame, font=("Arial", 18), width=25)
        self.username_entry_profile.pack(pady=10)

        tk.Label(self.profile_frame, text="New Password", font=("Arial", 18), bg="#34495e", fg="white").pack(pady=10)
        self.new_password_entry_profile = tk.Entry(self.profile_frame, font=("Arial", 18), show="*", width=25)
        self.new_password_entry_profile.pack(pady=10)

        tk.Button(self.profile_frame, text="Update Profile", font=("Arial", 18, "bold"), command=self.update_profile, bg="#2ecc71", fg="white", width=15).pack(pady=10)
        tk.Button(self.profile_frame, text="Back to Dashboard", font=("Arial", 18, "bold"), command=self.init_dashboard_page, bg="#e74c3c", fg="white", width=15).pack(pady=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        records = load_medical_records(file_path)
        if not records:
            messagebox.showerror("Error", "Failed to load medical records.")
            return

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summaries = []
        all_vitals = []

        for record in records:
            vitals = extract_vital_signs(record)
            all_vitals.append(vitals)

            if len(record.split()) > 20:  # Summarize only long records
                try:
                    summary = summarizer(record, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
                except Exception as e:
                    summary = f"Error summarizing record: {e}"
            else:
                summary = record

            summaries.append((summary, vitals if any(v != "Not Found" for v in vitals.values()) else None))

        self.display_summary(summaries)

    def display_summary(self, summaries):
        """Display summarized output with improved visuals."""
        self.clear_window()

        self.summary_frame = self.create_centered_frame("#008080")
        tk.Label(self.summary_frame, text="Summarized Output", font=("Arial", 32, "bold"), bg="#008080", fg="white").pack(pady=20)

        text_area = tk.Text(self.summary_frame, wrap=tk.WORD, font=("Arial", 16), width=100, height=25)
        for i, (summary, vitals) in enumerate(summaries):
            text_area.insert(tk.END, f"Record {i+1}:\n")
            text_area.insert(tk.END, f"Summary:\n{summary}\n")
            if vitals:
                text_area.insert(tk.END, "Vital Signs:\n")
                for key, value in vitals.items():
                    text_area.insert(tk.END, f"  {key}: {value}\n")
            text_area.insert(tk.END, "\n" + "-"*40 + "\n\n")
        text_area.pack(expand=True, fill=tk.BOTH)

        tk.Button(self.summary_frame, text="Back to Dashboard", font=("Arial", 18, "bold"), command=self.init_dashboard_page, bg="#3498db", fg="white").pack(pady=10)

    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if self.db is not None:  # Check if database connection is valid
            user = self.users_collection.find_one({"username": username, "password": password})
            if user:
                self.clear_window()  # Clear the window before showing the welcome message
                welcome_frame = self.create_centered_frame("#34495e")  # Frame for the welcome message
                welcome_message = f"Welcome {username}!"
                label = tk.Label(welcome_frame, text=welcome_message, font=("Arial", 24, "bold"), bg="#34495e", fg="white")
                label.pack(pady=20)
                
                # After the welcome message, you can call init_dashboard_page to proceed with the dashboard
                self.root.after(2000, self.init_dashboard_page)  # Show the dashboard after 2 seconds
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")
        else:
            messagebox.showerror("Error", "Database connection failed.")

    def register_user(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        if self.db is not None:  # Check if database connection is valid
            if self.users_collection.find_one({"username": username}):
                messagebox.showerror("Registration Failed", "Username already exists.")
            else:
                self.users_collection.insert_one({"username": username, "password": password})
                messagebox.showinfo("Registration Successful", "User registered successfully.")
                self.init_login_page()

    def update_profile(self):
        username = self.username_entry_profile.get()
        new_password = self.new_password_entry_profile.get()
        if self.db is not None:  # Check if database connection is valid
            self.users_collection.update_one({"username": username}, {"$set": {"password": new_password}})
            messagebox.showinfo("Profile Updated", "Your profile has been updated.")
            self.init_dashboard_page()

# Running the application
if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalApp(root)
    root.mainloop()
