import tkinter as tk
from tkinter import messagebox
import sqlite3
from gui import open_main_window  # this will link to your main expense GUI

# --- Database setup ---
conn = sqlite3.connect("bytebank.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')
conn.commit()
conn.close()

# --- Login Window ---
def login():
    username = entry_username.get()
    password = entry_password.get()

    conn = sqlite3.connect("bytebank.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        messagebox.showinfo("Success", f"Welcome {username}!")
        root.destroy()
        open_main_window(username)  # open the main app
    else:
        messagebox.showerror("Error", "Invalid username or password")

def register():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Please fill all fields")
        return

    conn = sqlite3.connect("bytebank.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", "Registration successful! You can log in now.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")
    conn.close()

# --- Tkinter UI ---
root = tk.Tk()
root.title("ByteBank Login")
root.geometry("400x300")
root.config(bg="black")

tk.Label(root, text="ByteBank Login", bg="black", fg="white", font=("Arial", 16, "bold")).pack(pady=20)

tk.Label(root, text="Username:", bg="black", fg="white").pack()
entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Password:", bg="black", fg="white").pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Login", command=login, bg="white", fg="black").pack(pady=10)
tk.Button(root, text="Register", command=register, bg="white", fg="black").pack()

root.mainloop()