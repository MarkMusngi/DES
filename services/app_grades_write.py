from flask import Flask, jsonify, request

# Node 5: Dedicated service for faculty to upload/update grades (Write only).
# This node is isolated from the read node to prevent blocking/slowdowns during large uploads.
app = Flask(__name__)

# --- API Endpoints ---
@app.route('/api/v1/grades/upload', methods=['POST'])
def upload_grades():
    """Allows authorized faculty to upload a batch of student grades."""
    data = request.json
    course_id = data.get('course_id')
    faculty_id = data.get('faculty_id') # Must be verified by Auth Service first (Role check)
    grades_batch = data.get('grades', [])

    # Mock authorization and data validation
    if not faculty_id:
        return jsonify({"status": "error", "message": "Unauthorized or Faculty ID missing"}), 401
    
    if not grades_batch:
        return jsonify({"status": "error", "message": "No grades provided in batch"}), 400

    # --- Persistence Logic Simulation ---
    # In a real system, this securely and transactionally updates the database.
    uploaded_count = len(grades_batch)
    
    print(f"Faculty {faculty_id} uploading {uploaded_count} grades for {course_id}. Data: {grades_batch}")

    return jsonify({
        "status": "success",
        "message": f"Successfully processed {uploaded_count} grades for {course_id}.",
        "course_id": course_id
    }), 200

if __name__ == '__main__':
    # Run on Port 5004 (Node 5)
    print("Starting Grades Write Service (Node 5) on Port 5004...")
    app.run(port=5004, debug=True)