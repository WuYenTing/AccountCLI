import cmd
import os
from auth import AuthDB
from db import DB
from getpass import getpass
from InquirerPy import inquirer
from tabulate import tabulate
from colorama import Fore, Style

class AccountingCLI(cmd.Cmd):
    intro = "Welcome to the Accounting CLI. Type help or ? to list commands."
    prompt = 'ACLI >>> '

    def __init__(self):
        super().__init__()
        self.auth = AuthDB()
        self.db = None
        self.user_id = None
        self.login_menu()

    def login_menu(self):
        while True:
            action = inquirer.select(
                message="Select an action:",
                choices=["Login", "Sign up"],
                default="Login"
            ).execute()

            username = input("Username: ").strip()
            password = getpass("Password: ").strip()

            if not username or not password:
                print("Username and password cannot be empty.")
                continue

            if action.lower() == 'sign up':
                if self.auth.create_user(username, password):
                    print("User created. Please login.")
                else:
                    print("Username already exists.")
            elif action.lower() == 'login':
                user_id = self.auth.authenticate_user(username, password)
                if user_id:
                    self.user_id = user_id
                    print(f"Welcome, {username}!")
                    user_db_file = f"data/{username}.db"
                    os.makedirs("data", exist_ok=True)
                    self.db = DB({"database": user_db_file})
                    break
                else:
                    print("Login failed.")

    def do_loadfile(self, filename):
        """Load records from a file (.txt, .csv, .json): loadfile [filename]"""
        import csv
        import json

        if not filename:
            print("Usage: loadfile [filename]")
            return

        if not os.path.isfile(filename):
            print(f"File not found: {filename}")
            return

        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        try:
            if ext == ".txt":
                with open(filename, 'r', encoding='utf-8') as f:
                    for lineno, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) < 3:
                            print(f"Line {lineno}: Invalid format")
                            continue
                        category_path = parts[0]
                        description = ' '.join(parts[1:-1])
                        amount = float(parts[-1])
                        self.db.add_record(category_path, description, amount)
                        print(f"Line {lineno}: Record added.")
            
            elif ext == ".csv":
                with open(filename, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for lineno, row in enumerate(reader, start=2):
                        try:
                            self.db.add_record(row['category'], row['description'], float(row['amount']))
                            print(f"Line {lineno}: Record added.")
                        except Exception as e:
                            print(f"Line {lineno}: Error - {e}")
            
            elif ext == ".json":
                with open(filename, encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        print("JSON must be a list of records.")
                        return
                    for idx, item in enumerate(data, start=1):
                        try:
                            self.db.add_record(item['category'], item['description'], float(item['amount']))
                            print(f"Record {idx}: Record added.")
                        except Exception as e:
                            print(f"Record {idx}: Error - {e}")
            
            else:
                print("Unsupported file type. Use .txt, .csv, or .json")

        except Exception as e:
            print(f"Failed to load file: {e}")

    def do_categories(self, arg):
        """Display all categories as a tree"""
        from collections import defaultdict

        def build_tree(paths):
            tree = lambda: defaultdict(tree)
            root = tree()
            for path in paths:
                parts = path.split('/')
                current = root
                for part in parts:
                    current = current[part]
            return root

        def print_tree(d, prefix=""):
            last = list(d.keys())[-1] if d else None
            for i, key in enumerate(d):
                is_last = (key == last)
                branch = "┗━ " if is_last else "┣━ "
                print(prefix + branch + key)
                extension = "    " if is_last else "┃   "
                print_tree(d[key], prefix + extension)

        # Fetch paths from DB
        self.db.cur.execute("SELECT path FROM categories ORDER BY path")
        rows = [row[0] for row in self.db.cur.fetchall()]
        tree = build_tree(rows)
        print_tree(tree)

    def do_list(self, arg):
        """List records by filter:
        list description [keyword]
        list date [YYYY-MM-DD]
        list category [category path]
        """
        parts = arg.strip().split(maxsplit=1)
        if len(parts) != 2:
            print("Usage:\n  list description [text]\n  list date [YYYY-MM-DD]\n  list category [path]")
            return

        field, value = parts
        if field == "description":
            results = self.db.find_records_by_field("description", value)
        elif field == "date":
            results = self.db.find_records_by_field("date", value)
        elif field == "category":
            results = self.db.find_records_by_field("category", value)
        else:
            print(f"Unsupported field: {field}")
            return

        if not results:
            print("No records found.")
            return

        print(tabulate(results, headers=["ID", "Category", "Description", "Amount", "Date"]))

    def do_add(self, arg):
        """Add a record: add [category/path] [description] [amount] [date?]
        Example: add expense/food/lunch 'chicken rice' 120 2025-05-01
                add expense/food/lunch 'chicken rice' 120  # uses today's date
        """
        parts = arg.split()
        if len(parts) < 3:
            print("Usage: add [category/path] [description] [amount] [date?]")
            return

        category_path = parts[0]

        try:
            amount = float(parts[-1])
            description = ' '.join(parts[1:-1])
            date = None  # Use DB default
        except ValueError:
            try:
                amount = float(parts[-2])
                description = ' '.join(parts[1:-2])
                date = parts[-1]  # User-supplied date
            except (ValueError, IndexError):
                print("Invalid format. Usage: add [category/path] [description] [amount] [date?]")
                return

        try:
            self.db.add_record(category_path, description, amount, date)
            print("Record added.")
        except Exception as e:
            print(f"Error adding record: {e}")

    def do_view(self, arg):
        """View all records"""
        records = self.db.view_records()
        print(tabulate(records, headers=["ID", "Category", "Description", "Amount"]))

    def do_delete(self, arg):
        """Delete records by category path"""
        if not arg:
            print("Usage: delete [category/path]")
            return
        self.db.delete_records_by_category(arg)
        print(f"Deleted records under category '{arg}'.")

    def do_find(self, arg):
        """Find records by category or description keyword"""
        if not arg:
            print("Usage: find [keyword]")
            return
        results = self.db.find_records(arg)
        print(tabulate(results, headers=["ID", "Category", "Description", "Amount"]))

    def do_exit(self, arg):
        """Exit the program"""
        print("Saving and exiting...")
        if self.db:
            self.db.close()
        self.auth.close()
        return True

    def do_EOF(self, arg):
        """Exit on Ctrl+D"""
        return self.do_exit(arg)

    def default(self, line):
        print(Fore.RED + f"Unknown command: {line}" + Style.RESET_ALL)

if __name__ == '__main__':
    AccountingCLI().cmdloop()