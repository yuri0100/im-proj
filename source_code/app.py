import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

# === Database Connection ===
# Update host/user/password/database if needed
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",       # default XAMPP root has no password
        database="cccs105"
    )
    cursor = conn.cursor(buffered=True)
except mysql.connector.Error as err:
    print("Error: Could not connect to database. Check MySQL status and credentials.")
    raise err

# === Helper Functions ===
def refresh_accounts():
    """Load accounts from DB into the Treeview."""
    for row in accounts_tree.get_children():
        accounts_tree.delete(row)
    try:
        cursor.execute("SELECT id, name, balance FROM accounts")
        for acct in cursor.fetchall():
            name = acct[1]
            balance = f"{acct[2]:.2f}"
            accounts_tree.insert("", "end", values=(name, balance, acct[0]))
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

def add_account():
    name = simpledialog.askstring("Add Account", "Enter new account name:")
    if name:
        try:
            cursor.execute("INSERT INTO accounts (name, balance) VALUES (%s, %s)", (name, 0.0))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add account:\n{e}")

def edit_account():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to edit.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    old_name = item['values'][0]
    new_name = simpledialog.askstring("Edit Account", f"New name for '{old_name}':", initialvalue=old_name)
    if new_name:
        try:
            cursor.execute("UPDATE accounts SET name=%s WHERE id=%s", (new_name, acct_id))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not rename account:\n{e}")

def delete_account():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to delete.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    acct_name = item['values'][0]
    if messagebox.askyesno("Confirm Delete", f"Delete account '{acct_name}' and all its transactions?"):
        try:
            cursor.execute("DELETE FROM transactions WHERE account_id=%s", (acct_id,))
            cursor.execute("DELETE FROM accounts WHERE id=%s", (acct_id,))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete account:\n{e}")

def open_transactions():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to view transactions.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    acct_name = item['values'][0]
    TransactionsWindow(root, acct_id, acct_name)

# === Transactions Window ===
class TransactionsWindow(tk.Toplevel):
    def __init__(self, master, account_id, account_name):
        super().__init__(master)
        self.title(f"Transactions - {account_name}")
        self.account_id = account_id
        self.geometry("600x400")

        # Transactions Table
        columns = ("Type", "Amount", "Date", "Note", "ID")
        self.trans_tree = ttk.Treeview(self, columns=columns, show='headings')
        self.trans_tree.heading("Type", text="Type")
        self.trans_tree.heading("Amount", text="Amount")
        self.trans_tree.heading("Date", text="Date")
        self.trans_tree.heading("Note", text="Note")
        self.trans_tree.heading("ID", text="ID")
        self.trans_tree.column("ID", width=0, stretch=False)  # hide ID column
        self.trans_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Add Transaction", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Transaction", command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Transaction", command=self.delete_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self.refresh_transactions()

    def refresh_transactions(self):
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        try:
            cursor.execute("SELECT id, type, amount, date, note FROM transactions WHERE account_id=%s", (self.account_id,))
            for tx in cursor.fetchall():
                tx_id, tx_type, amount, date, note = tx
                self.trans_tree.insert("", "end", values=(tx_type, f"{amount:.2f}", date, note, tx_id))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_transaction(self):
        TransactionDialog(self, self.account_id, None, self.refresh_transactions)

    def edit_transaction(self):
        selected = self.trans_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to edit.")
            return
        tx_id = self.trans_tree.item(selected)['values'][4]
        TransactionDialog(self, self.account_id, tx_id, self.refresh_transactions)

    def delete_transaction(self):
        selected = self.trans_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to delete.")
            return
        values = self.trans_tree.item(selected)['values']
        tx_id = values[4]
        tx_type = values[0]
        tx_amount = float(values[1])
        if messagebox.askyesno("Confirm Delete", "Delete this transaction?"):
            try:
                # Reverse the effect on balance
                if tx_type == "Deposit":
                    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id=%s", (tx_amount, self.account_id))
                else:
                    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id=%s", (tx_amount, self.account_id))
                cursor.execute("DELETE FROM transactions WHERE id=%s", (tx_id,))
                conn.commit()
                self.refresh_transactions()
                refresh_accounts()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete transaction:\n{e}")

# === Add/Edit Transaction Dialog ===
class TransactionDialog(tk.Toplevel):
    def __init__(self, master, account_id, transaction_id, refresh_callback):
        super().__init__(master)
        self.account_id = account_id
        self.transaction_id = transaction_id
        self.refresh_callback = refresh_callback
        self.title("Add Transaction" if transaction_id is None else "Edit Transaction")
        self.geometry("350x250")

        # Type
        tk.Label(self, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, values=["Deposit", "Withdrawal"], state="readonly")
        self.type_combo.grid(row=0, column=1, padx=5, pady=5)

        # Amount
        tk.Label(self, text="Amount:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_entry = tk.Entry(self)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5)

        # Date
        tk.Label(self, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_entry = tk.Entry(self)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)

        # Note
        tk.Label(self, text="Note:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.note_entry = tk.Entry(self)
        self.note_entry.grid(row=3, column=1, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Save", command=self.save_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # If editing, load existing values
        if self.transaction_id:
            cursor.execute("SELECT type, amount, date, note FROM transactions WHERE id=%s", (self.transaction_id,))
            tx = cursor.fetchone()
            if tx:
                self.type_var.set(tx[0])
                self.amount_entry.insert(0, f"{tx[1]:.2f}")
                self.date_entry.insert(0, tx[2].isoformat())
                self.note_entry.insert(0, tx[3])

    def save_transaction(self):
        tx_type = self.type_var.get()
        amount_str = self.amount_entry.get()
        date_str = self.date_entry.get()
        note = self.note_entry.get()

        # Validate fields
        if not tx_type or not amount_str or not date_str:
            messagebox.showwarning("Missing data", "Type, amount, and date are required.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except Exception as e:
            messagebox.showerror("Invalid Amount", str(e))
            return
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.")
            return

        # Get current balance
        cursor.execute("SELECT balance FROM accounts WHERE id=%s", (self.account_id,))
        current_balance = cursor.fetchone()[0]

        if self.transaction_id is None:
            # Add new transaction
            if tx_type == "Withdrawal" and amount > current_balance:
                messagebox.showerror("Overdraft", "Withdrawal exceeds current balance.")
                return
            try:
                if tx_type == "Deposit":
                    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id=%s", (amount, self.account_id))
                else:
                    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id=%s", (amount, self.account_id))
                cursor.execute(
                    "INSERT INTO transactions (account_id, type, amount, date, note) VALUES (%s, %s, %s, %s, %s)",
                    (self.account_id, tx_type, amount, date_obj, note)
                )
                conn.commit()
                self.refresh_callback()
                refresh_accounts()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not add transaction:\n{e}")
        else:
            # Edit existing transaction
            try:
                cursor.execute("SELECT type, amount FROM transactions WHERE id=%s", (self.transaction_id,))
                original_type, original_amount = cursor.fetchone()
                # Revert original effect
                if original_type == "Deposit":
                    new_balance = current_balance - original_amount
                else:
                    new_balance = current_balance + original_amount
                # Apply new effect
                if tx_type == "Deposit":
                    new_balance += amount
                else:
                    new_balance -= amount
                if new_balance < 0:
                    messagebox.showerror("Overdraft", "Change would make balance negative.")
                    return
                cursor.execute("UPDATE accounts SET balance = %s WHERE id=%s", (new_balance, self.account_id))
                cursor.execute(
                    "UPDATE transactions SET type=%s, amount=%s, date=%s, note=%s WHERE id=%s",
                    (tx_type, amount, date_obj, note, self.transaction_id)
                )
                conn.commit()
                self.refresh_callback()
                refresh_accounts()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not update transaction:\n{e}")

# === Main Window ===
root = tk.Tk()
root.title("Savings Ledger")
root.geometry("400x300")

# Accounts table
accounts_tree = ttk.Treeview(root, columns=("Name", "Balance", "ID"), show='headings')
accounts_tree.heading("Name", text="Account")
accounts_tree.heading("Balance", text="Balance")
accounts_tree.heading("ID", text="ID")
accounts_tree.column("ID", width=0, stretch=False)  # hide ID
accounts_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Buttons
btns = tk.Frame(root)
btns.pack(fill=tk.X, pady=5)
tk.Button(btns, text="Add Account", command=add_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="Edit Account", command=edit_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="Delete Account", command=delete_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="View Transactions", command=open_transactions).pack(side=tk.RIGHT, padx=5)

refresh_accounts()
root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

# === Database Connection ===
# Update host/user/password/database if needed
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",       # default XAMPP root has no password
        database="cccs105"
    )
    cursor = conn.cursor(buffered=True)
except mysql.connector.Error as err:
    print("Error: Could not connect to database. Check MySQL status and credentials.")
    raise err

# === Helper Functions ===
def refresh_accounts():
    """Load accounts from DB into the Treeview."""
    for row in accounts_tree.get_children():
        accounts_tree.delete(row)
    try:
        cursor.execute("SELECT id, name, balance FROM accounts")
        for acct in cursor.fetchall():
            name = acct[1]
            balance = f"{acct[2]:.2f}"
            accounts_tree.insert("", "end", values=(name, balance, acct[0]))
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

def add_account():
    name = simpledialog.askstring("Add Account", "Enter new account name:")
    if name:
        try:
            cursor.execute("INSERT INTO accounts (name, balance) VALUES (%s, %s)", (name, 0.0))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add account:\n{e}")

def edit_account():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to edit.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    old_name = item['values'][0]
    new_name = simpledialog.askstring("Edit Account", f"New name for '{old_name}':", initialvalue=old_name)
    if new_name:
        try:
            cursor.execute("UPDATE accounts SET name=%s WHERE id=%s", (new_name, acct_id))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not rename account:\n{e}")

def delete_account():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to delete.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    acct_name = item['values'][0]
    if messagebox.askyesno("Confirm Delete", f"Delete account '{acct_name}' and all its transactions?"):
        try:
            cursor.execute("DELETE FROM transactions WHERE account_id=%s", (acct_id,))
            cursor.execute("DELETE FROM accounts WHERE id=%s", (acct_id,))
            conn.commit()
            refresh_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete account:\n{e}")

def open_transactions():
    selected = accounts_tree.focus()
    if not selected:
        messagebox.showwarning("No selection", "Select an account to view transactions.")
        return
    item = accounts_tree.item(selected)
    acct_id = item['values'][2]
    acct_name = item['values'][0]
    TransactionsWindow(root, acct_id, acct_name)

# === Transactions Window ===
class TransactionsWindow(tk.Toplevel):
    def __init__(self, master, account_id, account_name):
        super().__init__(master)
        self.title(f"Transactions - {account_name}")
        self.account_id = account_id
        self.geometry("600x400")

        # Transactions Table
        columns = ("Type", "Amount", "Date", "Note", "ID")
        self.trans_tree = ttk.Treeview(self, columns=columns, show='headings')
        self.trans_tree.heading("Type", text="Type")
        self.trans_tree.heading("Amount", text="Amount")
        self.trans_tree.heading("Date", text="Date")
        self.trans_tree.heading("Note", text="Note")
        self.trans_tree.heading("ID", text="ID")
        self.trans_tree.column("ID", width=0, stretch=False)  # hide ID column
        self.trans_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Add Transaction", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Transaction", command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Transaction", command=self.delete_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self.refresh_transactions()

    def refresh_transactions(self):
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        try:
            cursor.execute("SELECT id, type, amount, date, note FROM transactions WHERE account_id=%s", (self.account_id,))
            for tx in cursor.fetchall():
                tx_id, tx_type, amount, date, note = tx
                self.trans_tree.insert("", "end", values=(tx_type, f"{amount:.2f}", date, note, tx_id))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_transaction(self):
        TransactionDialog(self, self.account_id, None, self.refresh_transactions)

    def edit_transaction(self):
        selected = self.trans_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to edit.")
            return
        tx_id = self.trans_tree.item(selected)['values'][4]
        TransactionDialog(self, self.account_id, tx_id, self.refresh_transactions)

    def delete_transaction(self):
        selected = self.trans_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to delete.")
            return
        values = self.trans_tree.item(selected)['values']
        tx_id = values[4]
        tx_type = values[0]
        tx_amount = float(values[1])
        if messagebox.askyesno("Confirm Delete", "Delete this transaction?"):
            try:
                # Reverse the effect on balance
                if tx_type == "Deposit":
                    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id=%s", (tx_amount, self.account_id))
                else:
                    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id=%s", (tx_amount, self.account_id))
                cursor.execute("DELETE FROM transactions WHERE id=%s", (tx_id,))
                conn.commit()
                self.refresh_transactions()
                refresh_accounts()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete transaction:\n{e}")

# === Add/Edit Transaction Dialog ===
class TransactionDialog(tk.Toplevel):
    def __init__(self, master, account_id, transaction_id, refresh_callback):
        super().__init__(master)
        self.account_id = account_id
        self.transaction_id = transaction_id
        self.refresh_callback = refresh_callback
        self.title("Add Transaction" if transaction_id is None else "Edit Transaction")
        self.geometry("350x250")

        # Type
        tk.Label(self, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, values=["Deposit", "Withdrawal"], state="readonly")
        self.type_combo.grid(row=0, column=1, padx=5, pady=5)

        # Amount
        tk.Label(self, text="Amount:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_entry = tk.Entry(self)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5)

        # Date
        tk.Label(self, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_entry = tk.Entry(self)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)

        # Note
        tk.Label(self, text="Note:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.note_entry = tk.Entry(self)
        self.note_entry.grid(row=3, column=1, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Save", command=self.save_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # If editing, load existing values
        if self.transaction_id:
            cursor.execute("SELECT type, amount, date, note FROM transactions WHERE id=%s", (self.transaction_id,))
            tx = cursor.fetchone()
            if tx:
                self.type_var.set(tx[0])
                self.amount_entry.insert(0, f"{tx[1]:.2f}")
                self.date_entry.insert(0, tx[2].isoformat())
                self.note_entry.insert(0, tx[3])

    def save_transaction(self):
        tx_type = self.type_var.get()
        amount_str = self.amount_entry.get()
        date_str = self.date_entry.get()
        note = self.note_entry.get()

        # Validate fields
        if not tx_type or not amount_str or not date_str:
            messagebox.showwarning("Missing data", "Type, amount, and date are required.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except Exception as e:
            messagebox.showerror("Invalid Amount", str(e))
            return
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.")
            return

        # Get current balance
        cursor.execute("SELECT balance FROM accounts WHERE id=%s", (self.account_id,))
        current_balance = cursor.fetchone()[0]

        if self.transaction_id is None:
            # Add new transaction
            if tx_type == "Withdrawal" and amount > current_balance:
                messagebox.showerror("Overdraft", "Withdrawal exceeds current balance.")
                return
            try:
                if tx_type == "Deposit":
                    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id=%s", (amount, self.account_id))
                else:
                    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id=%s", (amount, self.account_id))
                cursor.execute(
                    "INSERT INTO transactions (account_id, type, amount, date, note) VALUES (%s, %s, %s, %s, %s)",
                    (self.account_id, tx_type, amount, date_obj, note)
                )
                conn.commit()
                self.refresh_callback()
                refresh_accounts()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not add transaction:\n{e}")
        else:
            # Edit existing transaction
            try:
                cursor.execute("SELECT type, amount FROM transactions WHERE id=%s", (self.transaction_id,))
                original_type, original_amount = cursor.fetchone()
                # Revert original effect
                if original_type == "Deposit":
                    new_balance = current_balance - original_amount
                else:
                    new_balance = current_balance + original_amount
                # Apply new effect
                if tx_type == "Deposit":
                    new_balance += amount
                else:
                    new_balance -= amount
                if new_balance < 0:
                    messagebox.showerror("Overdraft", "Change would make balance negative.")
                    return
                cursor.execute("UPDATE accounts SET balance = %s WHERE id=%s", (new_balance, self.account_id))
                cursor.execute(
                    "UPDATE transactions SET type=%s, amount=%s, date=%s, note=%s WHERE id=%s",
                    (tx_type, amount, date_obj, note, self.transaction_id)
                )
                conn.commit()
                self.refresh_callback()
                refresh_accounts()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not update transaction:\n{e}")

# === Main Window ===
root = tk.Tk()
root.title("Savings Ledger")
root.geometry("400x300")

# Accounts table
accounts_tree = ttk.Treeview(root, columns=("Name", "Balance", "ID"), show='headings')
accounts_tree.heading("Name", text="Account")
accounts_tree.heading("Balance", text="Balance")
accounts_tree.heading("ID", text="ID")
accounts_tree.column("ID", width=0, stretch=False)  # hide ID
accounts_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Buttons
btns = tk.Frame(root)
btns.pack(fill=tk.X, pady=5)
tk.Button(btns, text="Add Account", command=add_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="Edit Account", command=edit_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="Delete Account", command=delete_account).pack(side=tk.LEFT, padx=5)
tk.Button(btns, text="View Transactions", command=open_transactions).pack(side=tk.RIGHT, padx=5)

refresh_accounts()
root.mainloop()
