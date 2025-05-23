# AccountCLI
project-name/
├── src/
│   ├── main.py
│   └── models.py
├── data/
│   └── database.db  # SQLite database file
├── config/
│   └── settings.py  # Configuration settings if needed
├── sql/
│   ├── setup.sql    # SQL script for initial database setup
│   └── seed.sql     # SQL script to seed the database with data
├── tests/
│   ├── test_models.py
│   └── test_db.py
├── docs/
│   └── setup_guide.md
├── README.md
└── requirements.txt

user table
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

category table
CREATE TABLE Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materialized_path TEXT NOT NULL,  -- Hierarchical representation
    name TEXT NOT NULL
);

transaction table
CREATE TABLE Transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,              -- Store date as ISO 8601 string
    category_id INTEGER NOT NULL,    -- Foreign key to Categories table
    item TEXT NOT NULL,
    amount REAL NOT NULL,            -- Represent income or expenditure
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES Categories(id)
);