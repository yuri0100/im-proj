Personal Savings Ledger Setup Instructions:

Install XAMPP – Ensure Apache and MySQL or MariaDB services are running

Create Database – Open phpMyAdmin or MySQL command line and execute the SQL statements in database/schema.sql to create the CCCS105 database and its tables

Populate Initial Data – Execute the statements in database/initial_data.sql to insert sample accounts and transactions

Configure Database Connection – Open source_code/config.env and set the DB_HOST, DB_USER, DB_PASS, and DB_NAME. For XAMPP, the default user is root with an empty password

Install Python Dependencies – Run pip install -r source_code/environment.txt to install required packages (mysql-connector-python)

Run the Application – In a terminal or command prompt, navigate to the source_code directory and run python app.py. The Tkinter GUI will launch

Usage:

Use the Accounts tab to add, edit, or delete savings accounts

Use the Transactions tab to record deposits and withdrawals linked to accounts

The account balance will auto-update based on transactions

