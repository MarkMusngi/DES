from flask import Flask, jsonify, request
from flask_cors import CORS
import grpc
import sys
sys.path.append('./generated')

import auth_pb2
import auth_pb2_grpc
import course_pb2
import course_pb2_grpc
import enrollment_pb2
import enrollment_pb2_grpc

app = Flask(__name__)
CORS(app)

# gRPC service addresses
AUTH_GRPC = 'localhost:50051'
COURSE_GRPC = 'localhost:50052'
ENROLLMENT_GRPC = 'localhost:50053'

# ============= AUTH ENDPOINTS =============

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.json
    try:
        with grpc.insecure_channel(AUTH_GRPC) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.Register(auth_pb2.RegisterRequest(
                username=data.get('username', ''),
                password=data.get('password', ''),
                role=data.get('role', 'student')
            ))
            
            if response.status == "success":
                return jsonify({
                    "status": response.status,
                    "message": response.message,
                    "token": response.token,
                    "user_id": response.user_id,
                    "role": response.role
                }), 201
            else:
                return jsonify({
                    "status": response.status,
                    "message": response.message
                }), 400 if response.status == "error" else 500
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Auth service unavailable"}), 503

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    try:
        with grpc.insecure_channel(AUTH_GRPC) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.Login(auth_pb2.LoginRequest(
                username=data.get('username', ''),
                password=data.get('password', '')
            ))
            
            if response.status == "success":
                return jsonify({
                    "status": response.status,
                    "message": response.message,
                    "token": response.token,
                    "user_id": response.user_id,
                    "role": response.role
                }), 200
            else:
                return jsonify({
                    "status": response.status,
                    "message": response.message
                }), 401
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Auth service unavailable"}), 503

@app.route('/api/v1/auth/validate', methods=['POST'])
def validate():
    data = request.json
    token = data.get('token', '')
    
    try:
        with grpc.insecure_channel(AUTH_GRPC) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.ValidateToken(auth_pb2.ValidateRequest(token=token))
            
            if response.status == "valid":
                return jsonify({
                    "status": response.status,
                    "user_id": response.user_id,
                    "role": response.role,
                    "username": response.username
                }), 200
            else:
                return jsonify({
                    "status": response.status,
                    "message": response.message
                }), 401
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Auth service unavailable"}), 503

# ============= COURSE ENDPOINTS =============

@app.route('/api/v1/courses', methods=['GET'])
def get_courses():
    try:
        with grpc.insecure_channel(COURSE_GRPC) as channel:
            stub = course_pb2_grpc.CourseServiceStub(channel)
            response = stub.GetCourses(course_pb2.GetCoursesRequest())
            
            if response.status == "success":
                courses = {}
                for course in response.courses:
                    courses[course.course_id] = {
                        "name": course.name,
                        "capacity": course.capacity,
                        "enrolled": course.enrolled,
                        "open": course.is_open
                    }
                return jsonify(courses), 200
            else:
                return jsonify({"status": response.status, "message": response.message}), 500
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Course service unavailable"}), 503

@app.route('/api/v1/courses/<course_id>', methods=['GET'])
def get_course_details(course_id):
    try:
        with grpc.insecure_channel(COURSE_GRPC) as channel:
            stub = course_pb2_grpc.CourseServiceStub(channel)
            response = stub.GetCourseDetails(course_pb2.CourseRequest(course_id=course_id))
            
            if response.status == "success" and response.course:
                return jsonify({
                    "status": "success",
                    "course": {
                        "course_id": response.course.course_id,
                        "name": response.course.name,
                        "capacity": response.course.capacity,
                        "enrolled": response.course.enrolled,
                        "open": response.course.is_open
                    }
                }), 200
            else:
                return jsonify({"status": response.status, "message": response.message}), 404
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Course service unavailable"}), 503

# ============= ENROLLMENT ENDPOINTS =============

@app.route('/api/v1/enroll/course/<course_id>', methods=['POST'])
def enroll_in_course(course_id):
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    if not token:
        return jsonify({"status": "error", "message": "Token missing"}), 401
    
    try:
        with grpc.insecure_channel(ENROLLMENT_GRPC) as channel:
            stub = enrollment_pb2_grpc.EnrollmentServiceStub(channel)
            response = stub.EnrollInCourse(enrollment_pb2.EnrollRequest(
                token=token,
                course_id=course_id
            ))
            
            if response.status == "success":
                return jsonify({"status": response.status, "message": response.message}), 200
            elif response.status == "rejected":
                return jsonify({"status": response.status, "message": response.message}), 403
            else:
                return jsonify({"status": response.status, "message": response.message}), 400
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Enrollment service unavailable"}), 503

@app.route('/api/v1/enrollments', methods=['GET'])
def get_enrollments():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    if not token:
        return jsonify({"status": "error", "message": "Token missing"}), 401
    
    try:
        with grpc.insecure_channel(ENROLLMENT_GRPC) as channel:
            stub = enrollment_pb2_grpc.EnrollmentServiceStub(channel)
            response = stub.GetStudentEnrollments(enrollment_pb2.StudentRequest(token=token))
            
            if response.status == "success":
                enrollments = []
                for enroll in response.enrollments:
                    enrollments.append({
                        "course_id": enroll.course_id,
                        "course_name": enroll.course_name,
                        "enrollment_date": enroll.enrollment_date
                    })
                return jsonify({
                    "status": "success",
                    "enrollments": enrollments
                }), 200
            else:
                return jsonify({"status": response.status, "message": response.message}), 400
    except grpc.RpcError as e:
        return jsonify({"status": "error", "message": "Enrollment service unavailable"}), 503

if __name__ == '__main__':
    print("REST Gateway starting on port 5001...")
    print("Translating REST calls to gRPC...")
    app.run(host='0.0.0.0', port=5001, debug=True)