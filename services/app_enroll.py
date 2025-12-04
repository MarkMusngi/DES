from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
import os
import jwt
from functools import wraps

# --- Configuration for Database and JWT ---
DB_NAME = os.getenv('POSTGRES_DB', 'student_portal_courses')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

# JWT Configuration (must match auth service)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super_secret_auth_key_12345')
JWT_ALGORITHM = "HS256"

# Node 4: Dedicated service for handling transactional enrollment
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Database Helper ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
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
        print(f"Database connection error: {e}")
        return None

# --- JWT Validation Decorator ---
def auth_required(f):
    """Validates JWT token locally and extracts user info."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from header
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                "status": "error", 
                "message": "Authentication required: Token is missing"
            }), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        # Validate JWT
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Attach user data to request
            request.user_id = payload.get('public_id')
            request.role = payload.get('role')
            request.username = payload.get('username')
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "invalid", 
                "message": "Token has expired"
            }), 401
        except jwt.InvalidSignatureError:
            return jsonify({
                "status": "invalid", 
                "message": "Invalid token signature"
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "invalid", 
                "message": "Invalid token"
            }), 401
        except Exception as e:
            print(f"Token validation error: {e}")
            return jsonify({
                "status": "error", 
                "message": "Token validation failed"
            }), 500

        return f(*args, **kwargs)
    return decorated

# --- Enrollment Endpoint ---
@app.route('/api/v1/enroll/course/<course_id>', methods=['POST'])
@auth_required
def enroll_in_course(course_id):
    """Handles the transactional process of enrolling a student in a course."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({
            "status": "error", 
            "message": "Database is unavailable. Enrollment cannot proceed."
        }), 503

    user_id_str = request.user_id
    user_role = request.role

    try:
        cur = conn.cursor(cursor_factory=DictCursor)

        # RBAC Check - Only students can enroll
        if user_role != 'student':
            print(f"Enrollment rejected: User {user_id_str} is '{user_role}', not a student")
            return jsonify({
                "status": "rejected", 
                "message": f"Enrollment is only allowed for students. Your role is '{user_role}'."
            }), 403

        # Check course details
        cur.execute("SELECT name, capacity, enrolled, is_open FROM courses WHERE course_id = %s;", (course_id,))
        course = cur.fetchone()

        if course is None:
            return jsonify({"status": "error", "message": f"Course ID {course_id} not found"}), 404

        current_enrolled = course['enrolled']
        max_capacity = course['capacity']
        is_open = course['is_open']

        # Validate course status
        if not is_open:
            return jsonify({"status": "error", "message": f"Course {course['name']} is not open for enrollment"}), 400

        if current_enrolled >= max_capacity:
            return jsonify({"status": "error", "message": f"Course {course['name']} is full"}), 400

        # Check if already enrolled
        cur.execute("SELECT 1 FROM enrollments WHERE student_public_id = %s AND course_id = %s;", 
                    (user_id_str, course_id))
        if cur.fetchone() is not None:
            print(f"Enrollment rejected: User {user_id_str} already enrolled in {course_id}")
            return jsonify({"status": "error", "message": f"You are already enrolled in {course['name']}"}), 400

        # Perform enrollment transaction
        cur.execute("UPDATE courses SET enrolled = enrolled + 1 WHERE course_id = %s;", (course_id,))
        cur.execute("""
            INSERT INTO enrollments (student_public_id, course_id)
            VALUES (%s, %s);
        """, (user_id_str, course_id))

        conn.commit()
        print(f"User {user_id_str} successfully enrolled in {course_id}")
        
        return jsonify({
            "status": "success", 
            "message": f"Successfully enrolled in {course['name']}. Welcome!"
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Enrollment transaction error: {e}")
        return jsonify({
            "status": "error", 
            "message": "An internal error occurred during enrollment"
        }), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Enrollment Service Node (Node 4) starting on port 5003...")
    print("\n=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print("=========================\n")
    app.run(host='0.0.0.0', port=5003, debug=True)