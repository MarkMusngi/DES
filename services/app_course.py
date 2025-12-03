from flask import Flask, jsonify
from common_jwt import token_required

app = Flask(__name__)

# Mock Data 
COURSES = {
    'CS101': {'name': 'Distributed Systems', 'status': 'Open', 'capacity': 50, 'enrolled': 45},
    'MATH205': {'name': 'Advanced Calculus', 'status': 'Open', 'capacity': 60, 'enrolled': 15},
    'ENG300': {'name': 'Technical Writing', 'status': 'Closed', 'capacity': 30, 'enrolled': 30},
}


@app.route('/api/v1/courses', methods=['GET'])
@token_required 
def get_available_courses():
    """
    Feature 2: View available courses. 
    This is now protected by JWT.
    """
    user_id = request.user_data['user_id']
    role = request.user_data['role']

    print(f"Access granted to user ID {user_id}, Role: {role}")
    
    return jsonify({
        "status": "success",
        "message": "Courses retrieved successfully",
        "user": {"id": user_id, "role": role},
        "courses": COURSES
    }), 200


if __name__ == '__main__':
    # Run on Port 5002 
    print("Starting Course Service (Node 3) on Port 5002...")
    app.run(port=5002, debug=True)