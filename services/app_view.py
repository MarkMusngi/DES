from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import requests 
import json


app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')
app.config['SECRET_KEY'] = 'a_view_node_secret_key_for_flask_sessions' 


AUTH_SERVICE_URL = 'http://127.0.0.1:5001'
COURSE_SERVICE_URL = 'http://127.0.0.1:5002'
# GRADES_READ_SERVICE_URL = 'http://127.0.0.1:5003'
# GRADES_WRITE_SERVICE_URL = 'http://127.0.0.1:5004'

@app.route('/')
def index():

    if 'jwt_token' in session:
        return redirect(url_for('courses_page'))
    return render_template('auth.html', endpoint='login')

@app.route('/courses')
def courses_page():
    if 'jwt_token' not in session:
        return redirect(url_for('index'))
    
    return render_template('courses.html')

@app.route('/logout')
def logout():
    session.pop('jwt_token', None)
    session.pop('user_role', None)
    return redirect(url_for('index'))



@app.route('/api/login', methods=['POST'])
def handle_login():
    """
    Proxies login request to the Auth Service (Node 2) and stores the JWT.
    """
    try:
        
        response = requests.post(f"{AUTH_SERVICE_URL}/api/v1/auth/login", json=request.json)
        
        if response.status_code == 200:
            data = response.json()
            session['jwt_token'] = data.get('token')
            session['user_role'] = data.get('role')
            return jsonify({"status": "success", "redirect": "/courses"}), 200
        else:
            return jsonify(response.json()), response.status_code

    except requests.exceptions.ConnectionError:
        # If service is unavailable
        return jsonify({
            "status": "error", 
            "message": "Authentication service is currently unavailable. Please try again later."
        }), 503 


@app.route('/api/courses', methods=['GET'])
def get_courses():
    """
    Proxies course request to the Course Service (Node 3), including the JWT.
    """
    if 'jwt_token' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    headers = {
        'Authorization': f"Bearer {session['jwt_token']}",
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{COURSE_SERVICE_URL}/api/v1/courses", headers=headers)
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.ConnectionError:
        # If service is unavailable
        return jsonify({
            "status": "error", 
            "message": "Course enrollment service is currently unavailable. Other features are still accessible."
        }), 503 


if __name__ == '__main__':
    # Run on Port 5000 
    print("Starting View Service (Node 1) on Port 5000...")
    print(f"Backend Services: Auth={AUTH_SERVICE_URL}, Course={COURSE_SERVICE_URL}")
    app.run(port=5000, debug=True)