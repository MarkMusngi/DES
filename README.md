# EduStream Distributed Student Portal

A robust, microservices-based academic platform designed for high-performance student and faculty management. The system utilizes a distributed node architecture, separating concerns across specialized gRPC servers.

***

## Key Features

* **Microservices Architecture:** Decoupled services for Authentication, Course Management, Enrollment, and Grading.
* **Hybrid Communication:** * **External:** REST API Gateway for frontend consumption.
    * **Internal:** Lightning-fast gRPC calls between service nodes.
* **Role-Based Access Control (RBAC):** * **Students:** Browse courses, enroll/drop classes, and view academic grades.
    * **Faculty:** Manage student lists and securely upload/update course grades.
* **Secure Session Management:** JWT-based authentication with local token validation across services to reduce latency.
* **Database Per Service:** Independent PostgreSQL instances for Auth and Academic data to ensure data isolation.



***

## Tech Stack

* **Frontend:** Flask (View Server), Tailwind CSS, JavaScript (Fetch API)
* **API Gateway:** Flask (REST Gateway)
* **Service Layer:** Python gRPC (Multiple Nodes)
* **Database:** PostgreSQL
* **Security:** JSON Web Tokens (JWT) & Werkzeug Password Hashing

***

## System Architecture (The Nodes)

| Node | Service | Technology | Port |
| :--- | :--- | :--- | :--- |
| **Node 1** | View Server | Flask / Templates | 5000 |
| **Node 2** | REST Gateway | Flask / gRPC Client | 5001 |
| **Node 3** | Auth Service | gRPC Server | 50051 |
| **Node 4** | Course Service | gRPC Server | 50052 |
| **Node 5** | Enrollment Service | gRPC Server | 50053 |
| **Node 6** | Grades Service | gRPC Server | 50054 |
| **Node 7** | Faculty Grades | gRPC Server | 50055 |



***

## Installation & Setup

Initialize the proto files using these command
cd services
mkdir -p generated
python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/auth.proto
python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/course.proto
python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/enrollment.proto
python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/grades.proto
python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated ./proto/faculty_grades.proto

Initialize the PostgreSQL Databases
psql -U postgres
CREATE DATABASE student_portal_auth;
CREATE DATABASE student_portal_courses;
CREATE DATABASE student_portal_grades;
\q

Run all services in seperate terminals (CMD)
python app_view.py
python grpc_auth_server.py
python grpc_course_server.py
python grpc_enrollment_server.py
python grpc_grades_server.py
python grpc_faculty_grades_server.py
python rest_gateway.py

After doing all the steps, run at http://localhost:5000.
