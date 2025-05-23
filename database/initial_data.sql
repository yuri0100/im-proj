-- initial_data.sql: Sample accounts and initial deposits
USE savings_db;
INSERT INTO accounts (name, balance) VALUES ('Cash', 1000.00), ('Bank', 5000.00);
INSERT INTO transactions (account_id, type, amount, date, note) VALUES
 (1, 'Deposit', 1000.00, '2025-01-01', 'Initial deposit'),
 (2, 'Deposit', 5000.00, '2025-01-01', 'Initial deposit');
