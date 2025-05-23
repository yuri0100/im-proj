-- schema.sql: Create database and tables for Savings Ledger
CREATE DATABASE IF NOT EXISTS savings_db;
USE savings_db;

CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    type ENUM('Deposit','Withdrawal') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    note VARCHAR(255),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);