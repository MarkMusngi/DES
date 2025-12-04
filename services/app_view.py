from flask import Flask, render_template

# Node 1: The View Server. Responsible for serving the static front-end (HTML, CSS, JS)
# and routing the user.

# Adjusting template_folder and static_folder paths relative to the 'services/' directory.
# templates are in '../frontend/templates', static files are in '../frontend/static'
app = Flask(__name__, 
            static_folder='../frontend/static', 
            template_folder='../frontend/templates')

@app.route('/')
def home():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/login')
def login_view():
    """Serves the login page, interacting with the Auth Service."""
    return render_template('auth.html', service_name="Auth Service Node")

@app.route('/courses')
def courses_view():
    """Serves the course view page, interacting with the Course Service."""
    return render_template('courses.html', service_name="Course Service Node")

@app.route('/enroll')
def enroll_page_view():
    """Serves the dedicated enrollment page (simulating a new Enrollment Service node)."""
    return render_template('enroll.html', 
                           service_name="Enrollment Service Node")

@app.route('/my_grades')
def grades_view():
    """Serves the student grades view page, interacting with the Grades Read Service."""
    return render_template('grades_view.html', service_name="Grades Read Service Node")

@app.route('/faculty/upload')
def grades_upload_view():
    """Serves the faculty grade upload page, interacting with the Grades Write Service."""
    return render_template('grades_upload.html', service_name="Grades Write Service Node")

if __name__ == '__main__':
    # Run on Port 5000 (Node 1)
    # IMPORTANT: You must run this file from the 'services/' directory for the relative paths to work correctly.
    print("Starting View Server (Node 1) on Port 5000...")
    app.run(port=5000, debug=True)