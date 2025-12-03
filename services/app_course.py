from flask import Flask, jsonify, request

# Node 3: Handles course catalog view and enrollment transaction logic.
app = Flask(__name__)

# --- Mock Data (Simulating persistence layer/Database) ---
COURSES = {
    "CS101": {"name": "Intro to Distributed Systems", "open": True, "capacity": 30, "enrolled": 28},
    "MATH203": {"name": "Calculus II", "open": True, "capacity": 50, "enrolled": 45},
    "ENG100": {"name": "Academic Writing", "open": False, "capacity": 20, "enrolled": 20}
}
ENROLLMENTS = {"101": ["CS101", "MATH203"]} 

# --- API Endpoints ---
@app.route('/api/v1/courses', methods=['GET'])
def get_courses():
    """Allows students to view the list of available courses."""
    return jsonify(COURSES), 200

@app.route('/api/v1/enroll', methods=['POST'])
def enroll_student():
    """Allows students to enroll in an open course."""
    data = request.json
    course_id = data.get('course_id')
    user_id = data.get('user_id') # Must be verified by Auth Service first

    course = COURSES.get(course_id)
    if not course:
        return jsonify({"status": "error", "message": "Course not found"}), 404
    
    if not course['open'] or course['enrolled'] >= course['capacity']:
        return jsonify({"status": "error", "message": "Course is full or closed"}), 400
    
    # Process enrollment transaction
    course['enrolled'] += 1
    ENROLLMENTS[str(user_id)] = ENROLLMENTS.get(str(user_id), []) + [course_id]
    
    print(f"User {user_id} enrolled in {course_id}. Enrolled count: {course['enrolled']}")
    
    return jsonify({"status": "success", "message": f"Successfully enrolled in {course_id}"}), 200

if __name__ == '__main__':
    # Run on Port 5002 (Node 3)
    print("Starting Course Service (Node 3) on Port 5002...")
    app.run(port=5002, debug=True)