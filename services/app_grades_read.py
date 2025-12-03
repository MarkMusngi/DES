from flask import Flask, jsonify, request

app = Flask(__name__)

STUDENT_GRADES = {
    "101": [
        {"course": "HIST101", "grade": "A-", "semester": "Fall 2023"},
        {"course": "CS100", "grade": "B+", "semester": "Fall 2023"},
        {"course": "MATH101", "grade": "A", "semester": "Spring 2024"},
    ],
    "102": [{"course": "ENG100", "grade": "C", "semester": "Fall 2023"}]
}


@app.route('/api/v1/grades/student/<int:user_id>', methods=['GET'])
def get_student_grades(user_id):
    """Retrieves all grades for a specific student ID."""

    grades = STUDENT_GRADES.get(str(user_id), [])
    
    if not grades:
        return jsonify({"status": "info", "message": f"No grades found for user {user_id}"}), 404

    return jsonify(grades), 200

if __name__ == '__main__':
    # Run on Port 5003 
    print("Starting Grades Read Service (Node 4) on Port 5003...")
    app.run(port=5003, debug=True)