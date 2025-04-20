from openai import OpenAI
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
from models import db, User, Project
from sqlalchemy.orm import Session

load_dotenv()  # Load .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)

# App configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-very-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/portfolio'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/projects'

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Debug: Check form data received
        print("DEBUG: Received POST request with form data")
        print(f"DEBUG: Username from form: {request.form.get('username')}")
        print(f"DEBUG: Password from form: {request.form.get('password')}")

        # Retrieve and clean username and password
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Check if username or password is blank
        if not username or not password:
            print("DEBUG: Username or password is blank")
            flash("Username and password cannot be blank.", "warning")
            return redirect(url_for('login'))

        # Fetch the user from the database
        user = User.query.filter_by(username=username).first()

        # Debug: Check if user was retrieved from the database
        print(f"DEBUG: User fetched from database: {user}")

        # Validate the user and the password
        if not user or not user.check_password(password):  # Ensure password matches
            print("DEBUG: Invalid username or password.")
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))

        # Debug: User is successfully authenticated
        print(f"DEBUG: User authenticated: {user.username}, Admin: {user.is_admin}")

        # Log the user in
        login_user(user)
        session['is_admin'] = user.is_admin  # Store admin status in session
        return redirect(url_for('admin_dashboard'))

    # Render login page for GET requests
    print("DEBUG: Rendering login page")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return render_template('403.html'), 403
    projects = Project.query.all()
    return render_template('admin_dashboard.html', projects=projects)


@app.route('/view_projects', methods=['GET'])
def view_projects():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 6, type=int)
        projects = Project.query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'projects': [{
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'image_url': project.image_url,
                'url': project.url,
                'created_at': project.created_at.isoformat()
            } for project in projects.items],
            'total': projects.total,
            'pages': projects.pages,
            'current_page': projects.page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        projects = Project.query.all()  # Fetch all projects from the database
        categories = {project.category for project in projects}
        return render_template('projects.html', projects=projects, categories = categories)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500



@app.route('/admin/add-project', methods=['POST', 'GET'])
def add_project():
    if request.method == 'GET':
        return render_template('add_project.html')
    try:
        # Validate form fields
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.files.get('image')
        category = request.form.get('category')

        # Validate category
        if not category:
            flash('Please select a category!', 'danger')
            return redirect(url_for('add_project'))
        if not title or not description or not image:
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate file type
        def allowed_file(filename):
            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if not allowed_file(image.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # Save the image
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(save_path)

        # Create and save the project
        new_project = Project(
            title=title.strip(),
            description=description.strip(),
            image_url=f"/static/projects/{filename}",  # Path for the saved image
            url=request.form.get('url', '').strip(),
            category=category.strip(),
            tags=request.form.get('tags', '').strip(),
            created_at=datetime.utcnow()
        )
        db.session.add(new_project)
        db.session.commit()

        flash('Project added successfully!', 'success')

        return jsonify({'message': 'Project created successfully', 'project_id': new_project.id}), 201

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
@app.route('/project_detail/<int:project_id>', methods=['GET'])
def project_detail(project_id):
    # Fetch project details from the database
    project = db.session.get(Project, project_id)
    return render_template('project_detail.html', project=project)

@app.route('/project/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    # Fetch the project by ID or return a 404 if not found
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        # Process form data for updating the project
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.url = request.form.get('url')
        project.tags = request.form.get('tags')
        project.category = request.form.get('category')

        # Handle the image update
        image = request.files.get('image')
        if image:
            # Save the new image and update the image URL
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            project.image_url = f"/static/projects/{filename}"

        # Save changes to the database
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('get_projects'))  # Redirect to the projects page

    # Render the edit form with the current project data for GET requests
    return render_template('edit_project.html', project=project)


@app.route('/project/delete/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    try:
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            flash('Project deleted successfully!', 'success')
        else:
            flash('Project not found.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/certificates')
def certificates():
    return render_template('certificates.html')  # This should exist in your templates folder

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()

    if not query:
        flash("Search query cannot be empty.", "warning")
        return redirect(url_for('home'))

    # Search projects by title or description (case-insensitive)
    results = Project.query.filter(
        Project.title.ilike(f"%{query}%") |
        Project.description.ilike(f"%{query}%")
    ).all()

    return render_template('search_results.html', query=query, results=results)

@app.route('/api/analytics/views')
def views_data():
    return jsonify({
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "data": [120, 190, 300, 150, 220, 170, 250]
    })

@app.route('/api/analytics/tags')
def tags_data():
    return jsonify({
        "labels": ["React", "Python", "AI", "ML", "Cybersecurity"],
        "data": [18, 22, 14, 19, 10]
    })

@app.route('/api/analytics/devices')
def devices_data():
    return jsonify({
        "labels": ["Desktop", "Mobile", "Tablet"],
        "data": [60, 30, 10]
    })

@app.route('/api/analytics/traffic')
def traffic_data():
    return jsonify({
        "labels": ["Direct", "Social", "Referral", "Search Engine"],
        "data": [45, 25, 15, 15]
    })


@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')


@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_input = data.get('message')
    print("User input received:", user_input)  # Debug

    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a portfolio website."},
                {"role": "user", "content": user_input}
            ]
        )
        response = completion.choices[0].message.content.strip()
        return jsonify({'response': response})
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': f"Internal error: {str(e)}"}), 500
@app.errorhandler(403)
def unauthorized(e):
    return render_template('403.html'), 403


# Create tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
