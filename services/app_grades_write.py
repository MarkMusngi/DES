from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/v1/grades/upload', methods=['POST'])
def upload_grades():
    """Allows authorized faculty to upload a batch of student grades."""
    data = request.json
    course_id = data.get('course_id')
    faculty_id = data.get('faculty_id') 
    grades_batch = data.get('grades', [])

    if not faculty_id:
        return jsonify({"status": "error", "message": "Unauthorized or Faculty ID missing"}), 401
    
    if not grades_batch:
        return jsonify({"status": "error", "message": "No grades provided in batch"}), 400

    uploaded_count = len(grades_batch)
    
    print(f"Faculty {faculty_id} uploading {uploaded_count} grades for {course_id}. Data: {grades_batch}")

    return jsonify({
        "status": "success",
        "message": f"Successfully processed {uploaded_count} grades for {course_id}.",
        "course_id": course_id
    }), 200

if __name__ == '__main__':
    # Run on Port 5004
    print("Starting Grades Write Service (Node 5) on Port 5004...")
    app.run(port=5004, debug=True)