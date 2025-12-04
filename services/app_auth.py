from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
import psycopg2
import uuid
import os

# Replace 'your_db_name', 'your_user', 'your_password' with actual credentials.
POSTGRES_DB = os.getenv('POSTGRES_DB', 'student_portal_auth')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

# A strong, securely stored secret key is essential for JWT integrity
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super_secret_auth_key_12345') 
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# Node 2: Dedicated service for handling user authentication (Login/Logout).
app = Flask(__name__)
CORS(app)
# --- Database Helper ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        print("Cannot initialize DB without a connection.")
        return

    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        public_id UUID UNIQUE NOT NULL,
        username VARCHAR(80) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'student'
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
        conn.commit()
        print("User table checked/created successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# --- JWT Functions ---
def generate_jwt(public_id, username, role):
    """Generates a secure JWT with user claims and expiration."""
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        'public_id': str(public_id),
        'username': username,
        'role': role,
        'exp': expiration_time,
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt(token):
    """Decodes and validates a JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {"status": "valid", "user_id": payload['public_id'], "role": payload['role'], "username": payload['username']}
    except jwt.ExpiredSignatureError:
        return {"status": "invalid", "message": "Token expired"}
    except jwt.InvalidSignatureError:
        return {"status": "invalid", "message": "Invalid token signature"}
    except jwt.InvalidTokenError:
        return {"status": "invalid", "message": "Invalid token"}


# --- API Endpoints ---

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Endpoint for new user registration."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student') 

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    conn = get_db_connection()
    if conn is None:
         return jsonify({"status": "error", "message": "Database connection error"}), 503

    try:
        # Hash the password securely
        password_hash = generate_password_hash(password)
        public_id = uuid.uuid4()
        
        with conn.cursor() as cur:
            insert_query = """
            INSERT INTO users (public_id, username, password_hash, role) 
            VALUES (%s, %s, %s, %s) RETURNING public_id;
            """
            cur.execute(insert_query, (str(public_id), username, password_hash, role)) 
            new_user_id = cur.fetchone()[0]

        conn.commit()
        
        token = generate_jwt(new_user_id, username, role) 
        
        return jsonify({
            "status": "success", 
            "message": f"User {username} successfully registered. Login token provided.",
            "token": token,
            "user_id": str(new_user_id),
            "role": role
        }), 201 # 201 Created

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"status": "error", "message": f"User '{username}' already exists"}), 409 # Conflict
    except Exception as e:
        conn.rollback()
        print(f"Registration error: {e}")
        return jsonify({"status": "error", "message": "An internal error occurred during registration"}), 500
    finally:
        conn.close()

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Endpoint for user login and JWT issuance."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    conn = get_db_connection()
    if conn is None:
         return jsonify({"status": "error", "message": "Database connection error"}), 503

    user = None
    try:
        with conn.cursor() as cur:
            select_query = """
            SELECT public_id, password_hash, role FROM users WHERE username = %s;
            """
            cur.execute(select_query, (username,))
            result = cur.fetchone()
            
            if result:
                user = {
                    "public_id": result[0],
                    "password_hash": result[1],
                    "role": result[2]
                }
    except Exception as e:
        print(f"Login query error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        conn.close()

    if user and check_password_hash(user['password_hash'], password):
        token = generate_jwt(user['public_id'], username, user['role'])
        
        print(f"User {username} logged in, generating token.")
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": token,
            "user_id": str(user['public_id']),
            "role": user['role']
        }), 200
        
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/v1/auth/validate', methods=['POST'])
def validate_token():
    """Endpoint for other services to validate a token before performing actions."""
    token = request.json.get('token')
    
    if not token:
        return jsonify({"status": "invalid", "message": "Token missing"}), 401
    
    validation_result = decode_jwt(token)
    
    if validation_result['status'] == 'valid':
        return jsonify({
            "status": "valid", 
            "user_id": validation_result['user_id'],
            "role": validation_result['role'],
            "username": validation_result['username']
        }), 200
        
    # All failure cases return 401 Unauthorized
    return jsonify(validation_result), 401

if __name__ == '__main__':
    # Initialize the database table when the service starts
    init_db()
    # Run on Port 5001 (Node 2)
    app.run(port=5001, debug=True)