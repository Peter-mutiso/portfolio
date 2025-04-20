from app import db, create_app  # Import your app factory if using Flask app factories
from models import User  # Ensure you import the correct User model
from werkzeug.security import generate_password_hash

def create_admin():
    # Create the admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        is_admin=True
    )
    admin_user.set_password("admin123")  # Hash the password
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created successfully!")

if __name__ == "__main__":
    app = create_app()  # Use your app factory function, if applicable
    with app.app_context():  # Set up the Flask application context
        create_admin()
