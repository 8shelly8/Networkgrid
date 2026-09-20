 CREATE TABLE employee_vault (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50),
        role VARCHAR(50),
        secret_note TEXT
    );

    INSERT INTO employee_vault (username, role, secret_note) VALUES
    ('shepherd', 'System Architect', 'Remember to rotate the golden collar every 30 days.'),
    ('admin_backup', 'Database Admin', 'FLAG:you got to the database. this is the end'),
    ('j_doe', 'Junior Dev', 'Left the test credentials on internal staging.');
