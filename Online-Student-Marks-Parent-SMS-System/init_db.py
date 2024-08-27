import sqlite3
conn = sqlite3.connect('school.db')
cursor = conn.cursor()

cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')
cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_contact TEXT NOT NULL
        )
        ''')
cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            mark INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
        ''')

# Insert sample data into students table
students_data = [
    (1001, 'Ayush Pundir', '+917078946163'),
    (1002, 'Lakshay Garg', '+917078946163'),
    (1003, 'Rajvansh Singh Chauhan', '+917078946163'),
    (1004, 'Rudransh Pokhriyal', '+917078946163')
]

cursor.executemany('''
INSERT INTO students (student_id, name, parent_contact)
VALUES (?, ?, ?)
''', students_data)

# Insert sample data into marks table
marks_data = [
    (1001, 'Math', 75),
    (1001, 'English', 45),
    (1002, 'Math', 85),
    (1002, 'English', 55),
    (1003, 'Math', 56),
    (1003, 'English', 65),
    (1004, 'Math', 90),
    (1004, 'English', 70)
]

cursor.executemany('''
INSERT INTO marks (student_id, subject, mark)
VALUES (?, ?, ?)
''', marks_data)

conn.commit()
conn.close()

print("Database initialized and sample data inserted successfully.")
