import cmd
import sqlite3
import bcrypt
import curses

def main_menu(stdscr):
    curses.curs_set(0)  # Hide cursor


class AccountCLI(cmd.Cmd):
    prompt = '> '
    current_user = None

    def preloop(self):
        # Initialize the user database and add a sample user
        self.initialize_user_db()
        # Start with the curses UI for login/register
        choice = curses.wrapper(main_menu)
        if choice == "login":
            self.do_login(input("Enter username and password: "))
        elif choice == "register":
            self.do_register(input("Enter username and password: "))

    def initialize_user_db(self):
        conn = sqlite3.connect('users.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS Users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL
                        )''')
        conn.commit()
        conn.close()

    def do_register(self, args):
        """Register a new user: register [username] [password]"""
        try:
            username, password = args.split()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            conn = sqlite3.connect('users.db')
            conn.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            print(f"User {username} registered successfully.")
        except ValueError:
            print("Usage: register [username] [password]")
        except sqlite3.IntegrityError:
            print("Username already exists.")
    
    def do_login(self, args):
        """Login a user: login [username] [password]"""
        try:
            username, password = args.split()
            conn = sqlite3.connect('users.db')
            cursor = conn.execute("SELECT password_hash FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
                self.current_user = username
                print(f"{username} logged in successfully.")
                self.prompt = f'{username}@accountcli> '
            else:
                print("Authentication failed.")
        except ValueError:
            print("Usage: login [username] [password]")

    def do_logout(self, args):
        """Logout the current user"""
        if self.current_user:
            print(f"{self.current_user} logged out.")
            self.current_user = None
            self.prompt = '> '
        else:
            print("No user is currently logged in.")

    def do_exit(self, args):
        """Exit the command line interface"""
        print("Exiting...")
        return True  # Return True to exit the cmd loop

    def emptyline(self):
        pass

if __name__ == '__main__':
    AccountCLI().cmdloop()