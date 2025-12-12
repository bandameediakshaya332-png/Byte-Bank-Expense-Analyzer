import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, filedialog
from datetime import datetime
import sqlite3
import csv
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

DB_NAME = "bytebank.db"

# ---------------- Database helpers ----------------
def get_conn():
    return sqlite3.connect(DB_NAME)

def setup_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

setup_db()

# ---------------- Login / Register Window ----------------
def start_login_window():
    login_root = tk.Tk()
    login_root.title("ByteBank — Login / Register")
    login_root.geometry("420x300")
    login_root.configure(bg="black")

    tk.Label(login_root, text="ByteBank Login", font=("Helvetica", 18, "bold"),
             fg="white", bg="black").pack(pady=12)

    frame = tk.Frame(login_root, bg="black")
    frame.pack(pady=6)

    tk.Label(frame, text="Username:", fg="white", bg="black").grid(row=0, column=0, sticky="w", padx=5, pady=6)
    entry_user = tk.Entry(frame, width=28)
    entry_user.grid(row=0, column=1, padx=5, pady=6)

    tk.Label(frame, text="Password:", fg="white", bg="black").grid(row=1, column=0, sticky="w", padx=5, pady=6)
    entry_pass = tk.Entry(frame, show="*", width=28)
    entry_pass.grid(row=1, column=1, padx=5, pady=6)

    def register():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()
        if not username or not password:
            messagebox.showwarning("Input error", "Please enter username and password", parent=login_root)
            return
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful. You can now login.", parent=login_root)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.", parent=login_root)
        finally:
            conn.close()

    def login():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()
        if not username or not password:
            messagebox.showwarning("Input error", "Please enter username and password", parent=login_root)
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            login_root.destroy()
            open_main_window(username)
        else:
            messagebox.showerror("Login failed", "Invalid username or password", parent=login_root)

    btn_frame = tk.Frame(login_root, bg="black")
    btn_frame.pack(pady=10)

    btn_style = {"width": 12, "bg": "white", "fg": "black", "font": ("Helvetica", 11, "bold"), "bd": 0, "activebackground": "#e0e0e0"}
    tk.Button(btn_frame, text="Login", command=login, **btn_style).grid(row=0, column=0, padx=8)
    tk.Button(btn_frame, text="Register", command=register, **btn_style).grid(row=0, column=1, padx=8)

    tk.Label(login_root, text="(Register a new user first if you don't have an account)",
             fg="gray", bg="black", font=("Helvetica", 9)).pack(pady=8)

    login_root.mainloop()

# ---------------- Main App Window ----------------
def open_main_window(username):
    setup_db()

    app = tk.Tk()
    app.title(f"ByteBank — {username}")
    app.geometry("640x620")
    app.configure(bg="black")

    header = tk.Label(app, text=f"ByteBank Expense Analyzer — {username}",
                      font=("Helvetica", 18, "bold"), fg="white", bg="black")
    header.pack(pady=12)

    def valid_category_input(prompt, default=None):
        valid_categories = ["Food", "Transport", "Rent", "Bills", "Others"]
        while True:
            ans = simpledialog.askstring("Category", prompt, initialvalue=default, parent=app)
            if ans is None:
                return None
            if ans.strip() and ans.title() in valid_categories:
                return ans.title()
            else:
                messagebox.showerror("Invalid", f"Choose category: {', '.join(valid_categories)}", parent=app)

    # ---- CRUD Operations ----
    def add_expense():
        while True:
            date_input = simpledialog.askstring("Date", "Enter date (YYYY-MM-DD) or leave empty for today:", parent=app)
            if date_input is None: return
            if not date_input:
                date_input = datetime.today().strftime("%Y-%m-%d")
                break
            try:
                datetime.strptime(date_input, "%Y-%m-%d")
                break
            except ValueError:
                messagebox.showerror("Invalid", "Enter date in YYYY-MM-DD format.", parent=app)

        category = valid_category_input("Enter category (Food, Transport, Rent, Bills, Others):")
        if category is None: return

        description = simpledialog.askstring("Description", "Enter description (optional):", parent=app)

        while True:
            amount_input = simpledialog.askstring("Amount", "Enter amount (positive number):", parent=app)
            if amount_input is None: return
            try:
                amount = float(amount_input)
                if amount <= 0: raise ValueError
                break
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid positive number.", parent=app)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO expenses (user, date, category, description, amount) VALUES (?, ?, ?, ?, ?)",
                    (username, date_input, category, description or "", amount))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Expense added.", parent=app)

    def view_expenses():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, date, category, description, amount FROM expenses WHERE user=? ORDER BY date DESC, id DESC", (username,))
        rows = cur.fetchall()
        conn.close()

        win = tk.Toplevel(app)
        win.title("All Expenses")
        win.geometry("700x480")
        win.configure(bg="white")
        st = scrolledtext.ScrolledText(win, width=95, height=28)
        st.pack(padx=8, pady=8)
        st.insert(tk.END, "ID | Date       | Category   | Description                     | Amount\n")
        st.insert(tk.END, "-"*95 + "\n")
        for r in rows:
            rid, date, cat, desc, amt = r
            desc = (desc[:30] + "...") if desc and len(desc) > 33 else (desc or "")
            st.insert(tk.END, f"{rid:3} | {date:10} | {cat:9} | {desc:30} | {amt:.2f}\n")
        st.configure(state="disabled")

    def update_expense():
        try:
            id_str = simpledialog.askstring("Update", "Enter Expense ID to update (see View to find ID):", parent=app)
            if id_str is None: return
            exp_id = int(id_str)
        except ValueError:
            messagebox.showerror("Invalid", "Enter a valid integer ID.", parent=app)
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, date, category, description, amount FROM expenses WHERE id=? AND user=?", (exp_id, username))
        r = cur.fetchone()
        conn.close()
        if not r:
            messagebox.showerror("Not found", "Expense ID not found for your account.", parent=app)
            return

        _, date_old, cat_old, desc_old, amt_old = r
        date_new = simpledialog.askstring("Date", f"Enter new date ({date_old}) or leave empty to keep:", parent=app) or date_old
        try:
            datetime.strptime(date_new, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid", "Date must be YYYY-MM-DD.", parent=app)
            return

        category_new = valid_category_input(f"Enter new category ({cat_old}) or cancel to keep:")
        if category_new is None: category_new = cat_old

        description_new = simpledialog.askstring("Description", f"Enter new description or leave empty to keep:", parent=app)
        if description_new is None or description_new.strip() == "": description_new = desc_old

        amt_input = simpledialog.askstring("Amount", f"Enter new amount ({amt_old}) or leave empty to keep:", parent=app)
        if amt_input is None or amt_input.strip() == "": amount_new = amt_old
        else:
            try:
                amount_new = float(amt_input)
                if amount_new <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Enter valid positive amount.", parent=app)
                return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""UPDATE expenses SET date=?, category=?, description=?, amount=? WHERE id=? AND user=?""",
                    (date_new, category_new, description_new, amount_new, exp_id, username))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Expense updated.", parent=app)

    def delete_expense():
        try:
            id_str = simpledialog.askstring("Delete", "Enter Expense ID to delete (see View to find ID):", parent=app)
            if id_str is None: return
            exp_id = int(id_str)
        except ValueError:
            messagebox.showerror("Invalid", "Enter a valid integer ID.", parent=app)
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM expenses WHERE id=? AND user=?", (exp_id, username))
        r = cur.fetchone()
        conn.close()
        if not r:
            messagebox.showerror("Not found", "Expense ID not found for your account.", parent=app)
            return

        if not messagebox.askyesno("Confirm", f"Delete expense ID {exp_id}?"): return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id=? AND user=?", (exp_id, username))
        conn.commit()
        conn.close()
        messagebox.showinfo("Deleted", f"Expense ID {exp_id} deleted.", parent=app)

    def filter_expenses():
        choice = simpledialog.askstring("Filter", "Filter by (category/date):", parent=app)
        if choice is None: return
        choice = choice.strip().lower()
        conn = get_conn()
        cur = conn.cursor()
        if choice == "category":
            cat = simpledialog.askstring("Category", "Enter category to filter by:", parent=app)
            if cat is None: conn.close(); return
            cur.execute("SELECT id, date, category, description, amount FROM expenses WHERE user=? AND LOWER(category)=? ORDER BY date DESC",
                        (username, cat.lower().title()))
        elif choice == "date":
            dateq = simpledialog.askstring("Date", "Enter date (YYYY-MM-DD) to filter:", parent=app)
            if dateq is None: conn.close(); return
            try: datetime.strptime(dateq, "%Y-%m-%d")
            except ValueError: messagebox.showerror("Invalid", "Date must be YYYY-MM-DD.", parent=app); conn.close(); return
            cur.execute("SELECT id, date, category, description, amount FROM expenses WHERE user=? AND date=? ORDER BY id DESC", (username, dateq))
        else:
            messagebox.showerror("Invalid", "Enter 'category' or 'date'.", parent=app)
            conn.close(); return

        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("No results", "No expenses found for that filter.", parent=app)
            return

        win = tk.Toplevel(app)
        win.title("Filtered Expenses")
        win.geometry("700x480")
        win.configure(bg="white")
        st = scrolledtext.ScrolledText(win, width=95, height=28)
        st.pack(padx=8, pady=8)
        st.insert(tk.END, "ID | Date       | Category   | Description                     | Amount\n")
        st.insert(tk.END, "-"*95 + "\n")
        for r in rows:
            rid, date, cat, desc, amt = r
            desc = (desc[:30] + "...") if desc and len(desc) > 33 else (desc or "")
            st.insert(tk.END, f"{rid:3} | {date:10} | {cat:9} | {desc:30} | {amt:.2f}\n")
        st.configure(state="disabled")

    def summarize_expenses():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT SUM(amount) FROM expenses WHERE user=?", (username,))
        total = cur.fetchone()[0] or 0.0
        cur.execute("SELECT category, SUM(amount) FROM expenses WHERE user=? GROUP BY category", (username,))
        rows = cur.fetchall()
        conn.close()
        text = f"Total Expenses: {total:.2f}\n\nCategory-wise breakdown:\n"
        for cat, amt in rows:
            text += f"{cat}: {amt:.2f}\n"
        messagebox.showinfo("Summary", text, parent=app)

    # --------- Matplotlib Graphs ---------
    def plot_category_expenses():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT category, SUM(amount) FROM expenses WHERE user=? GROUP BY category", (username,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No expenses to plot.", parent=app)
            return

        categories, amounts = zip(*rows)
        fig = Figure(figsize=(5,5), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90, colors=['#555','#888','#aaa','#ccc','#eee'])
        ax.set_title(f"{username}'s Expenses by Category")

        win = tk.Toplevel(app)
        win.title("Category-wise Expenses")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def plot_date_expenses():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT date, SUM(amount) FROM expenses WHERE user=? GROUP BY date ORDER BY date", (username,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No expenses to plot.", parent=app)
            return

        dates, amounts = zip(*rows)
        fig = Figure(figsize=(6,4), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(dates, amounts, color='black')
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45)
        ax.set_xlabel("Date")
        ax.set_ylabel("Amount")
        ax.set_title(f"{username}'s Expenses Over Time")

        win = tk.Toplevel(app)
        win.title("Date-wise Expenses")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    # --------- CSV Export ---------
    def export_csv():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, date, category, description, amount FROM expenses WHERE user=? ORDER BY date DESC", (username,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("No data", "No expenses to export.", parent=app)
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], parent=app)
        if not fpath:
            return
        try:
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID","Date","Category","Description","Amount"])
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Exported", f"Expenses exported to {os.path.basename(fpath)}", parent=app)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}", parent=app)

    def about():
        messagebox.showinfo("About", "ByteBank — Digital Expense Analyzer\nDeveloped by: Akshaya\nTechnologies: Python, Tkinter, SQLite", parent=app)

    def exit_app():
        if messagebox.askyesno("Exit", "Exit ByteBank?"):
            app.destroy()

    # ---------------- Buttons ----------------
    btn_opts = {"width": 34, "bg": "white", "fg": "black", "font": ("Helvetica", 12, "bold"), "bd": 0, "activebackground": "#e0e0e0"}

    tk.Button(app, text="1. Add Expense", command=add_expense, **btn_opts).pack(pady=6)
    tk.Button(app, text="2. View Expenses", command=view_expenses, **btn_opts).pack(pady=6)
    tk.Button(app, text="3. Update Expense", command=update_expense, **btn_opts).pack(pady=6)
    tk.Button(app, text="4. Delete Expense", command=delete_expense, **btn_opts).pack(pady=6)
    tk.Button(app, text="5. Filter Expenses", command=filter_expenses, **btn_opts).pack(pady=6)
    tk.Button(app, text="6. Summarize Expenses", command=summarize_expenses, **btn_opts).pack(pady=6)
    tk.Button(app, text="7. Category-wise Graph", command=plot_category_expenses, **btn_opts).pack(pady=6)
    tk.Button(app, text="8. Date-wise Graph", command=plot_date_expenses, **btn_opts).pack(pady=6)
    tk.Button(app, text="9. Export to CSV", command=export_csv, **btn_opts).pack(pady=6)
    tk.Button(app, text="10. About", command=about, **btn_opts).pack(pady=6)
    tk.Button(app, text="11. Exit", command=exit_app, **btn_opts).pack(pady=12)

    app.mainloop()