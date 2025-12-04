# course_service.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid

# Configuration
DB_NAME = os.getenv('POSTGRES_DB', 'student_portal_courses')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

def get_db_connection():
    """Return a psycopg2 connection or None if failed."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"[Node 3] Database connection error: {e}")
        return None

def check_or_create_tables():
    """Ensure schema exists and insert initial data if empty."""
    conn = get_db_connection()
    if conn is None:
        print("[Node 3] FATAL: Could not connect to database at startup.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                course_id VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                capacity INTEGER NOT NULL,
                enrolled INTEGER DEFAULT 0,
                is_open BOOLEAN DEFAULT TRUE
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                student_public_id UUID NOT NULL,
                course_id VARCHAR(10) NOT NULL REFERENCES courses(course_id),
                enrollment_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (student_public_id, course_id)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                student_public_id UUID NOT NULL,
                course_id VARCHAR(10) NOT NULL REFERENCES courses(course_id),
                grade VARCHAR(5),
                UNIQUE (student_public_id, course_id)
            );
            """)

            # Insert initial data only if courses table empty
            cur.execute("SELECT COUNT(*) FROM courses;")
            count = cur.fetchone()[0]
            if count == 0:
                initial_courses = [
                    ("CS101", "Intro to Computer Science", 42, True),
                    ("MATH203", "Calculus II", 45, True),
                    ("ENG100", "Academic Writing", 40, True),
                    ("GERIZAL", "Life and Works of Rizal", 43, True),
                    ("GEETHIC", "Ethics and Morality", 41, True)
                ]
                insert_query = """
                INSERT INTO courses (course_id, name, capacity, is_open)
                VALUES (%s, %s, %s, %s);
                """
                cur.executemany(insert_query, initial_courses)
                print("[Node 3] Inserted initial courses.")
        conn.commit()
        print("[Node 3] Tables checked/created successfully.")
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"[Node 3] Database setup failed: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/api/v1/courses', methods=['GET'])
def get_courses():
    """
    Public read-only endpoint returning a mapping of course_id -> course data.
    Returns 503 if DB dependency is down.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({
            "status": "error",
            "message": "Course Service: Database dependency is down (Node 3 failure)"
        }), 503

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT course_id, name, capacity, enrolled, is_open FROM courses ORDER BY course_id;")
            rows = cur.fetchall()

            courses = {}
            for r in rows:
                courses[r['course_id']] = {
                    "name": r['name'],
                    "open": bool(r['is_open']),
                    "capacity": int(r['capacity']),
                    "enrolled": int(r['enrolled'])
                }

            return jsonify(courses), 200

    except Exception as e:
        print(f"[Node 3] Error fetching courses: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_or_create_tables()
    print("Starting Course View Service (Node 3) on Port 5002...")
    # Host 0.0.0.0 so other services (or docker containers) can reach it
    app.run(host='0.0.0.0', port=5002, debug=True)
