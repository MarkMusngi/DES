import grpc
from concurrent import futures
import sys
sys.path.append('./generated')

import course_pb2
import course_pb2_grpc

import psycopg2
from psycopg2.extras import DictCursor
import os

# Configuration
POSTGRES_DB = os.getenv('POSTGRES_DB', 'student_portal_courses')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '1234')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        return None

def init_db():
    """Initialize courses database with sample data"""
    conn = get_db_connection()
    if conn is None:
        print("Cannot initialize DB without a connection.")
        return

    try:
        with conn.cursor() as cur:
            # Create courses table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    capacity INTEGER NOT NULL,
                    enrolled INTEGER DEFAULT 0,
                    is_open BOOLEAN DEFAULT TRUE
                );
            """)
            
            # Create enrollments table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id SERIAL PRIMARY KEY,
                    student_public_id UUID NOT NULL,
                    course_id VARCHAR(20) NOT NULL,
                    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_public_id, course_id)
                );
            """)
            
            # Insert sample courses if they don't exist
            cur.execute("SELECT COUNT(*) FROM courses;")
            if cur.fetchone()[0] == 0:
                sample_courses = [
                    ('CS101', 'Introduction to Computer Science', 30, 0, True),
                    ('MATH203', 'Calculus III', 25, 0, True),
                    ('ENG100', 'English Composition', 20, 0, True),
                    ('GERIZAL', 'Rizal: Life and Works', 35, 0, True),
                    ('GEETHIC', 'Ethics', 30, 0, True),
                ]
                cur.executemany(
                    "INSERT INTO courses (course_id, name, capacity, enrolled, is_open) VALUES (%s, %s, %s, %s, %s);",
                    sample_courses
                )
                print("Sample courses inserted.")
        
        conn.commit()
        print("Course database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

class CourseServiceServicer(course_pb2_grpc.CourseServiceServicer):
    
    def GetCourses(self, request, context):
        """Get all available courses"""
        conn = get_db_connection()
        if conn is None:
            return course_pb2.GetCoursesResponse(
                status="error",
                message="Database connection error",
                courses=[]
            )
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT course_id, name, capacity, enrolled, is_open 
                    FROM courses 
                    ORDER BY course_id;
                """)
                rows = cur.fetchall()
                
                courses = []
                for row in rows:
                    course_info = course_pb2.CourseInfo(
                        course_id=row['course_id'],
                        name=row['name'],
                        capacity=row['capacity'],
                        enrolled=row['enrolled'],
                        is_open=row['is_open']
                    )
                    courses.append(course_info)
                
                return course_pb2.GetCoursesResponse(
                    status="success",
                    message="Courses retrieved successfully",
                    courses=courses
                )
        
        except Exception as e:
            print(f"Error fetching courses: {e}")
            return course_pb2.GetCoursesResponse(
                status="error",
                message="Internal server error",
                courses=[]
            )
        finally:
            conn.close()
    
    def GetCourseDetails(self, request, context):
        """Get details of a specific course"""
        course_id = request.course_id
        
        conn = get_db_connection()
        if conn is None:
            return course_pb2.CourseResponse(
                status="error",
                message="Database connection error",
                course=None
            )
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT course_id, name, capacity, enrolled, is_open 
                    FROM courses 
                    WHERE course_id = %s;
                """, (course_id,))
                row = cur.fetchone()
                
                if row is None:
                    return course_pb2.CourseResponse(
                        status="error",
                        message=f"Course {course_id} not found",
                        course=None
                    )
                
                course_info = course_pb2.CourseInfo(
                    course_id=row['course_id'],
                    name=row['name'],
                    capacity=row['capacity'],
                    enrolled=row['enrolled'],
                    is_open=row['is_open']
                )
                
                return course_pb2.CourseResponse(
                    status="success",
                    message="Course details retrieved",
                    course=course_info
                )
        
        except Exception as e:
            print(f"Error fetching course details: {e}")
            return course_pb2.CourseResponse(
                status="error",
                message="Internal server error",
                course=None
            )
        finally:
            conn.close()

def serve():
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    course_pb2_grpc.add_CourseServiceServicer_to_server(CourseServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("gRPC Course Service starting on port 50052...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()