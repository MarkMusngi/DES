from flask import Flask, jsonify, request
import jwt
import datetime
from common_jwt import SECRET_KEY, ALGORITHM, EXPIRY_HOURS
import time

app = Flask(__name__)


def generate_jwt(user_id, role):
    """Generates a secure JWT for session tracking."""
    # Set expiration time
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=EXPIRY_HOURS)
    
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': expiration_time,
        'iat': datetime.datetime.now(datetime.timezone.utc) 
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if (username == "student" and password == "password") or \
       (username == "faculty" and password == "password"):
        user_id = 101 if username == "student" else 500
        role = "student" if username == "student" else "faculty"
        
        token = generate_jwt(user_id, role)
        
        print(f"User {username} logged in, generating real JWT.")
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": token,
            "user_id": user_id,
            "role": role
        }), 200
        
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/v1/auth/validate', methods=['POST'])
def validate_token():

    token = request.json.get('token')
    
    if not token:
        return jsonify({"status": "invalid", "message": "Token missing"}), 403
    
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return jsonify({"status": "valid", "user_id": data['user_id'], "role": data['role']}), 200
    except Exception as e:
        print(f"Validation failed: {e}")
        return jsonify({"status": "invalid", "message": str(e)}), 403

if __name__ == '__main__':
    # Run on Port 5001 
    print("Starting Auth Service (Node 2) on Port 5001...")
    app.run(port=5001, debug=True)