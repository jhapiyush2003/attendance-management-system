import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime

# Database setup
def create_tables():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    date TEXT,
                    present INTEGER,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )''')
    conn.commit()
    conn.close()

# CRUD operations
def add_student(name):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        messagebox.showinfo("Success", f"Student {name} added.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Student already exists.")
    conn.close()

def remove_student(name):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE name = ?", (name,))
    c.execute("DELETE FROM attendance WHERE student_id IN (SELECT id FROM students WHERE name = ?)", (name,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", f"Student {name} removed.")

def get_students():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT name FROM students ORDER BY name")
    students = [row[0] for row in c.fetchall()]
    conn.close()
    return students

def mark_attendance(attendance_data, date):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    for student, present in attendance_data.items():
        c.execute("SELECT id FROM students WHERE name = ?", (student,))
        student_id = c.fetchone()[0]
        c.execute("INSERT INTO attendance (student_id, date, present) VALUES (?, ?, ?)", (student_id, date, 1 if present else 0))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Attendance marked for " + date)

def generate_summary():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("""
        SELECT s.name, COUNT(a.present) as total_days, SUM(a.present) as present_days
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id, s.name
    """)
    summary = c.fetchall()
    conn.close()
    summary_text = "Attendance Summary:\n\n"
    for name, total, present in summary:
        percentage = (present / total * 100) if total > 0 else 0
        summary_text += f"{name}: {present}/{total} days ({percentage:.1f}%)\n"
    return summary_text

# GUI
class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Attendance Management System")
        create_tables()
        self.students = get_students()
        self.check_vars = {}
        self.create_widgets()

    def create_widgets(self):
        # Frame for student management
        manage_frame = tk.Frame(self.root)
        manage_frame.pack(pady=10)

        tk.Label(manage_frame, text="Student Name:").grid(row=0, column=0)
        self.student_entry = tk.Entry(manage_frame)
        self.student_entry.grid(row=0, column=1)
        tk.Button(manage_frame, text="Add Student", command=self.add_student).grid(row=0, column=2)
        tk.Button(manage_frame, text="Remove Student", command=self.remove_student).grid(row=0, column=3)

        # Listbox for students
        self.student_listbox = tk.Listbox(manage_frame, height=10, width=30)
        self.student_listbox.grid(row=1, column=0, columnspan=4, pady=10)
        self.update_student_list()

        # Frame for attendance marking
        attend_frame = tk.Frame(self.root)
        attend_frame.pack(pady=10)

        tk.Label(attend_frame, text="Mark Attendance").pack()
        self.attend_canvas = tk.Canvas(attend_frame, height=200)
        self.attend_canvas.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar = tk.Scrollbar(attend_frame, orient=tk.VERTICAL, command=self.attend_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.attend_canvas.configure(yscrollcommand=scrollbar.set)
        self.attend_inner_frame = tk.Frame(self.attend_canvas)
        self.attend_canvas.create_window((0, 0), window=self.attend_inner_frame, anchor="nw")
        self.attend_inner_frame.bind("<Configure>", lambda e: self.attend_canvas.configure(scrollregion=self.attend_canvas.bbox("all")))

        self.update_checkboxes()

        tk.Button(attend_frame, text="Submit Attendance", command=self.submit_attendance).pack(pady=10)

        # Summary button
        tk.Button(self.root, text="Generate Summary", command=self.show_summary).pack(pady=10)

    def update_student_list(self):
        self.student_listbox.delete(0, tk.END)
        for student in self.students:
            self.student_listbox.insert(tk.END, student)

    def update_checkboxes(self):
        for widget in self.attend_inner_frame.winfo_children():
            widget.destroy()
        self.check_vars = {}
        for i, student in enumerate(self.students):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.attend_inner_frame, text=student, variable=var)
            chk.pack(anchor=tk.W)
            self.check_vars[student] = var

    def add_student(self):
        name = self.student_entry.get().strip()
        if name:
            add_student(name)
            self.students = get_students()
            self.update_student_list()
            self.update_checkboxes()
            self.student_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Enter a student name.")

    def remove_student(self):
        selected = self.student_listbox.curselection()
        if selected:
            name = self.student_listbox.get(selected[0])
            remove_student(name)
            self.students = get_students()
            self.update_student_list()
            self.update_checkboxes()
        else:
            messagebox.showerror("Error", "Select a student to remove.")

    def submit_attendance(self):
        date = simpledialog.askstring("Date", "Enter date (YYYY-MM-DD):", initialvalue=datetime.now().strftime("%Y-%m-%d"))
        if date:
            attendance_data = {student: var.get() for student, var in self.check_vars.items()}
            mark_attendance(attendance_data, date)
            # Reset checkboxes
            for var in self.check_vars.values():
                var.set(False)

    def show_summary(self):
        summary = generate_summary()
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Attendance Summary")
        text = tk.Text(summary_window, wrap=tk.WORD)
        text.insert(tk.END, summary)
        text.pack(expand=True, fill=tk.BOTH)
        tk.Button(summary_window, text="Close", command=summary_window.destroy).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
