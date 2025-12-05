from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
import requests
from functools import wraps
import os
import jwt
from datetime import datetime, timezone

app = Flask(__name__, 
            static_folder='frontend/static', 
            template_folder='frontend/templates')

app.secret_key = 'your_secret_key_here_change_in_production'

REST_GATEWAY_URL = os.getenv('REST_GATEWAY_URL', 'http://localhost:5001/api/v1') 
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super_secret_auth_key_12345')
JWT_ALGORITHM = "HS256"

print(f"Using REST Gateway URL: {REST_GATEWAY_URL}")

def is_token_valid(token):
    """Check if JWT token is still valid"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return True
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session or 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_view'))
        
        if not is_token_valid(session.get('token')):
            flash('Your session has expired. Please log in again.', 'warning')
            session.clear()
            return redirect(url_for('login_view'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    """Serves the main dashboard page (requires login)"""
    return render_template('index.html', 
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/login')
def login_view():
    """Serves the login page"""
    if 'token' in session and is_token_valid(session.get('token')):
        return redirect(url_for('home'))
    return render_template('auth.html', service_name="Auth Service Node")

@app.route('/api/login', methods=['POST'])
def login():
    """Handle login via REST Gateway"""
    data = request.get_json()
    
    try:
        response = requests.post(
            f'{REST_GATEWAY_URL}/auth/login',
            json=data,
            timeout=5
        )
        
        result = response.json()
        
        if response.ok and result.get('status') == 'success':
            session['token'] = result['token']
            session['username'] = data['username']
            session['role'] = result['role']
            session['user_id'] = result['user_id']
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'role': result['role']
            }), 200
        else:
            return jsonify(result), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': 'Auth service unavailable'
        }), 503

@app.route('/api/register', methods=['POST'])
def register():
    """Handle registration via REST Gateway"""
    data = request.get_json()
    
    try:
        response = requests.post(
            f'{REST_GATEWAY_URL}/auth/register',
            json=data,
            timeout=5
        )
        
        result = response.json()
        
        if response.ok and result.get('status') == 'success':
            session['token'] = result['token']
            session['username'] = data['username']
            session['role'] = result['role']
            session['user_id'] = result['user_id']
            
            return jsonify({
                'status': 'success',
                'message': 'Registration successful',
                'role': result['role']
            }), 201
        else:
            return jsonify(result), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': 'Auth service unavailable'
        }), 503

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('login_view'))

@app.route('/courses')
@login_required
def courses_view():
    """Serves the course view page"""
    return render_template('courses.html', 
                           service_name="Course Service Node",
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/enroll')
@login_required
def enroll_page_view():
    """Serves the enrollment page"""
    return render_template('enroll.html', 
                           service_name="Enrollment Service Node",
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/my_grades')
@login_required
def grades_view():
    """Serves the student grades view page"""
    return render_template('grades_view.html', 
                           service_name="Grades Read Service Node",
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/faculty/upload')
@login_required
def grades_upload_view():
    """Serves the faculty grade upload page"""
    if session.get('role') != 'faculty':
        return render_template('access_denied.html',
                               username=session.get('username'),
                               role=session.get('role')), 403
    
    return render_template('grades_upload.html', 
                           service_name="Grades Write Service Node",
                           username=session.get('username'),
                           role=session.get('role'))

@app.route('/api/proxy/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def proxy_api(endpoint):
    """Proxy API calls to REST Gateway with token from session"""
    token = session.get('token')
    
    if not is_token_valid(token):
        return jsonify({
            'status': 'error',
            'message': 'Your session has expired. Please log in again.'
        }), 401
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f'{REST_GATEWAY_URL}/{endpoint}'
    
    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        try:
            return jsonify(response.json()), response.status_code
        except requests.exceptions.JSONDecodeError:
            print(f"Warning: Non-JSON response from REST Gateway for {url}: {response.text[:100]}...")
            return jsonify({
                'status': 'error', 
                'message': f'Invalid response format from REST Gateway (Status {response.status_code})'
            }), 500
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Service unavailable: {str(e)}'
        }), 503

if __name__ == '__main__':
    print("=" * 70)
    print("Starting View Server (Node 1) on Port 5000...")
    print("=" * 70)
    print("Features:")
    print("  - Session-based authentication")
    print("  - Token validation on each request")
    print("  - Login required for all pages except /login")
    print("  - Logout button on all authenticated pages")
    print("  - Automatic token management")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)