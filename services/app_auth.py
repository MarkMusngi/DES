from flask import Flask, jsonify, request
import time

# Node 2: Dedicated service for handling user authentication (Login/Logout).
# This service is critical for generating and validating sessions (JWTs).
app = Flask(__name__)

# --- Mock Data/Functions ---
def generate_jwt(user_id):
    """Securely generates a mock JWT for session tracking across nodes."""
    # The current time is included to simulate expiration/session tracking.
    timestamp = int(time.time())
    return f"mock_jwt_for_user_{user_id}_{timestamp}.sig"

# --- API Endpoints ---
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Mock validation: only 'student/pass' or 'faculty/admin' are valid
    if (username == "student" and password == "pass") or \
       (username == "faculty" and password == "admin"):
        user_id = 101 if username == "student" else 500
        role = "student" if username == "student" else "faculty"
        token = generate_jwt(user_id)
        
        print(f"User {username} logged in, generating token: {token}")
        
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
    """Endpoint for other services to validate a token before performing actions."""
    token = request.json.get('token')
    # Simple check for mock token validity
    if token and "mock_jwt_for_user" in token:
        # In a real app, JWT is decoded and validity (expiration, signature) is checked
        user_id = token.split('_')[3]
        return jsonify({"status": "valid", "user_id": user_id}), 200
        
    return jsonify({"status": "invalid", "message": "Token expired or invalid"}), 403

if __name__ == '__main__':
    # Run on Port 5001 (Node 2)
    print("Starting Auth Service (Node 2) on Port 5001...")
    app.run(port=5001, debug=True)