from flask import Blueprint, jsonify
from models import Project, BlogPost

# Define Blueprint for project routes
project_routes = Blueprint('project_routes', __name__)

@project_routes.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        projects = Project.query.all()
        if not projects:
            return jsonify({'message': 'No projects found'}), 404
        project_list = [{
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'image_url': project.image_url
        } for project in projects]
        return jsonify({
            'total_projects': len(project_list),
            'projects': project_list
        }), 200
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

# Define Blueprint for blog routes
blog_routes = Blueprint('blog_routes', __name__)

@blog_routes.route('/api/blog', methods=['GET'])
def get_blog_posts():
    try:
        posts = BlogPost.query.all()
        if not posts:
            return jsonify({'message': 'No blog posts found'}), 404
        post_list = [{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'date_posted': post.date_posted.isoformat()  # Serialize datetime to string
        } for post in posts]
        return jsonify({
            'total_posts': len(post_list),
            'posts': post_list
        }), 200
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500
