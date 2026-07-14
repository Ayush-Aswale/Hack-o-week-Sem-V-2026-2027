import sqlite3
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
DB_NAME = 'students.db'

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    We set row_factory = sqlite3.Row so we can access columns by name (like a dictionary).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database by creating the 'students' table if it doesn't already exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            branch TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database table when the Flask app starts
init_db()

@app.route('/')
def index():
    """
    Serves the main frontend page (index.html).
    Flask automatically looks for this inside the 'templates' directory.
    """
    return render_template('index.html')

@app.route('/students', methods=['GET'])
def get_students():
    """
    GET API: Fetches all students from the database.
    Returns a JSON list of all student objects.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to standard Python dictionaries
    students = []
    for row in rows:
        students.append({
            'id': row['id'],
            'name': row['name'],
            'age': row['age'],
            'branch': row['branch'],
            'email': row['email']
        })
        
    return jsonify(students), 200

@app.route('/students', methods=['POST'])
def add_student():
    """
    POST API: Adds a new student record to the database.
    Expects request payload: { "name": "...", "age": ..., "branch": "...", "email": "..." }
    """
    data = request.get_json()
    
    # Simple validation checks
    if not data or not all(k in data for k in ('name', 'age', 'branch', 'email')):
        return jsonify({'error': 'Missing required fields (name, age, branch, email)'}), 400
        
    name = data['name'].strip()
    age = data['age']
    branch = data['branch'].strip()
    email = data['email'].strip()
    
    # Validation helper checks
    if not name or not branch or not email:
        return jsonify({'error': 'Fields cannot be empty or whitespaces only'}), 400
        
    try:
        age_val = int(age)
        if age_val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Age must be a positive integer'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO students (name, age, branch, email) VALUES (?, ?, ?, ?)',
            (name, age_val, branch, email)
        )
        conn.commit()
        # Fetch the newly created ID
        new_id = cursor.lastrowid
        conn.close()
        
        # Return the created student data
        return jsonify({
            'id': new_id,
            'name': name,
            'age': age_val,
            'branch': branch,
            'email': email,
            'message': 'Student added successfully'
        }), 201
        
    except sqlite3.IntegrityError:
        conn.close()
        # A UNIQUE constraint violation on the 'email' column throws this error
        return jsonify({'error': 'A student with this email address already exists'}), 400

@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """
    PUT API: Updates an existing student record by ID.
    Expects request payload: { "name": "...", "age": ..., "branch": "...", "email": "..." }
    """
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'age', 'branch', 'email')):
        return jsonify({'error': 'Missing required fields for update'}), 400
        
    name = data['name'].strip()
    age = data['age']
    branch = data['branch'].strip()
    email = data['email'].strip()
    
    if not name or not branch or not email:
        return jsonify({'error': 'Fields cannot be empty'}), 400
        
    try:
        age_val = int(age)
        if age_val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Age must be a positive integer'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if student exists
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': f'Student with ID {student_id} not found'}), 404
        
    try:
        cursor.execute(
            'UPDATE students SET name = ?, age = ?, branch = ?, email = ? WHERE id = ?',
            (name, age_val, branch, email, student_id)
        )
        conn.commit()
        conn.close()
        return jsonify({
            'id': student_id,
            'name': name,
            'age': age_val,
            'branch': branch,
            'email': email,
            'message': 'Student updated successfully'
        }), 200
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Another student with this email address already exists'}), 400

@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """
    DELETE API: Deletes a student record by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if student exists
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': f'Student with ID {student_id} not found'}), 404
        
    cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
    student_name = cursor.fetchone()['name']
    
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'Student {student_name} deleted successfully'}), 200

if __name__ == '__main__':
    # Start the Flask development server
    # debug=True automatically reloads the application when code changes
    app.run(debug=True, port=5000)
