import sys
import os
import logging
from models import db, Project
from app import app


# ✅ Ensure the correct project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.info(f"Python Path Updated: {sys.path}")

def add_sample_projects():
    """Add sample projects to the database if none exist."""
    try:
        with app.app_context():
            if Project.query.count() == 0:
                sample_projects = [
                    Project(title="Machine Learning Project",
                            description="A predictive model for stock prices.",
                            image_url="https://example.com/image1.jpg"),
                    Project(title="Web Design Project",
                            description="A responsive portfolio website.",
                            image_url="https://example.com/image2.jpg")
                ]
                db.session.bulk_save_objects(sample_projects)
                db.session.commit()
                logging.info("✅ Sample projects added successfully!")
            else:
                logging.info("📌 Sample projects already exist. Skipping insertion.")
    except Exception as e:
        logging.error(f"❌ Error adding sample projects: {e}")

def init_db():
    """Initialize the database."""
    try:
        with app.app_context():
            db.create_all()
            logging.info("✅ Database tables created successfully!")
            add_sample_projects()
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")

with app.app_context():
    db.create_all()
    print("Database initialized successfully!")


if __name__ == '__main__':
    init_db()
