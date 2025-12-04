from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/test')
def test():
    return jsonify({"message": "Test route works!"}), 200

@app.route('/api/v1/enroll/course/<course_id>', methods=['POST'])
def enroll_in_course(course_id):
    return jsonify({
        "status": "success",
        "message": f"Test enrollment for {course_id}",
        "note": "This is a minimal test without auth"
    }), 200

if __name__ == '__main__':
    print("Starting MINIMAL enrollment test service on port 5003...")
    print("\n=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print("=========================\n")
    app.run(host='0.0.0.0', port=5003, debug=True)