import grpc
from concurrent import futures
import sys
sys.path.append('./generated')

import auth_pb2
import auth_pb2_grpc

from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
import psycopg2
import uuid
import os

# Configuration
POSTGRES_DB = os.getenv('POSTGRES_DB', 'student_portal_auth')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super_secret_auth_key_12345')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

def get_db_connection():
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

def generate_jwt(public_id, username, role):
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

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    
    def Register(self, request, context):
        username = request.username
        password = request.password
        role = request.role or 'student'

        if not username or not password:
            return auth_pb2.AuthResponse(
                status="error",
                message="Missing username or password",
                token="",
                user_id="",
                role=""
            )

        conn = get_db_connection()
        if conn is None:
            return auth_pb2.AuthResponse(
                status="error",
                message="Database connection error",
                token="",
                user_id="",
                role=""
            )

        try:
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
            
            return auth_pb2.AuthResponse(
                status="success",
                message=f"User {username} successfully registered",
                token=token,
                user_id=str(new_user_id),
                role=role
            )

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return auth_pb2.AuthResponse(
                status="error",
                message=f"User '{username}' already exists",
                token="",
                user_id="",
                role=""
            )
        except Exception as e:
            conn.rollback()
            print(f"Registration error: {e}")
            return auth_pb2.AuthResponse(
                status="error",
                message="An internal error occurred during registration",
                token="",
                user_id="",
                role=""
            )
        finally:
            conn.close()

    def Login(self, request, context):
        username = request.username
        password = request.password

        if not username or not password:
            return auth_pb2.AuthResponse(
                status="error",
                message="Missing username or password",
                token="",
                user_id="",
                role=""
            )

        conn = get_db_connection()
        if conn is None:
            return auth_pb2.AuthResponse(
                status="error",
                message="Database connection error",
                token="",
                user_id="",
                role=""
            )

        try:
            with conn.cursor() as cur:
                select_query = """
                SELECT public_id, password_hash, role FROM users WHERE username = %s;
                """
                cur.execute(select_query, (username,))
                result = cur.fetchone()
                
                if result and check_password_hash(result[1], password):
                    user = {
                        "public_id": result[0],
                        "role": result[2]
                    }
                    token = generate_jwt(user['public_id'], username, user['role'])
                    
                    return auth_pb2.AuthResponse(
                        status="success",
                        message="Login successful",
                        token=token,
                        user_id=str(user['public_id']),
                        role=user['role']
                    )
                else:
                    return auth_pb2.AuthResponse(
                        status="error",
                        message="Invalid credentials",
                        token="",
                        user_id="",
                        role=""
                    )
        except Exception as e:
            print(f"Login error: {e}")
            return auth_pb2.AuthResponse(
                status="error",
                message="Internal server error",
                token="",
                user_id="",
                role=""
            )
        finally:
            conn.close()

    def ValidateToken(self, request, context):
        token = request.token
        
        if not token:
            return auth_pb2.ValidateResponse(
                status="invalid",
                message="Token missing",
                user_id="",
                role="",
                username=""
            )
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return auth_pb2.ValidateResponse(
                status="valid",
                message="Token is valid",
                user_id=payload['public_id'],
                role=payload['role'],
                username=payload['username']
            )
        except jwt.ExpiredSignatureError:
            return auth_pb2.ValidateResponse(
                status="invalid",
                message="Token expired",
                user_id="",
                role="",
                username=""
            )
        except jwt.InvalidTokenError:
            return auth_pb2.ValidateResponse(
                status="invalid",
                message="Invalid token",
                user_id="",
                role="",
                username=""
            )

def serve():
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Auth Service starting on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()