# Standard Libraries
import os
import tempfile
import subprocess
import re
import base64

# Flask Libraries
from flask import render_template, request, redirect, url_for, Response, session, send_from_directory, jsonify
from . import app, mongo
from .utilities import file_storage

# Constants
CONTENT_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.html': 'text/html'
}


def is_supported_file_type(filename):
    ext = os.path.splitext(filename)[-1]
    return ext in CONTENT_TYPES


# ---------- HOME ROUTES ----------

@app.route('/')
def index():
    user = mongo.db.users.find_one({"name": "admin"})   
    if user:
        user_info = f"Database is connected -- added Type: {user['type']}, Name: {user['name']}"
    else:
        user_info = "Database error: User not found!"
    return render_template("index.html", user_info=user_info)


# ---------- UPLOAD ROUTES ----------

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    temp_file_path = session.get('temp_file_path', None)
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return 'No file part', 400
        temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(temp_file_path)
        session['temp_file_path'] = temp_file_path
    return render_template("upload.html", temp_file_path=temp_file_path)

@app.route('/session_file_info')
def get_session_file_info():
    file_name = session.get('filename')
    file_id = session.get('file_id')
    project_id = session.get('project_id')
    file_type = '.' + (file_name.split('.')[-1] if file_name else 'Empty')
    temp_file_path = session.get('temp_file_path')  

    return jsonify({
        'filename': file_name if file_name else 'Empty',
        'filetype': file_type,
        'file_id': file_id if file_id else 'Empty',
        'project_id': project_id if project_id else 'Empty',
        'temp_file_path': temp_file_path if temp_file_path else 'Empty'
    })


# ---------- FILE MANAGEMENT ROUTES ----------
def save_temp_file(file_data):
    # Save the file to the system's temp directory
    temp_path = os.path.join(tempfile.gettempdir(), file_data['filename'])
    with open(temp_path, 'wb') as f:
        f.write(file_data['file_object'].read())
    return temp_path

@app.route('/display/<file_id>')
def display_file(file_id):
    file_data = file_storage.get_file_by_id(file_id)
    # Ensure file_data has the expected data
    if not file_data or 'file_object' not in file_data:
        return jsonify({'error': 'Document not found'}), 404

    # Extract file object and filename from the dictionary
    file_obj = file_data['file_object']
    filename = file_data['filename']
    
    ext = os.path.splitext(filename)[-1]

    # Checking file type
    if not is_supported_file_type(filename):
        print("Unsupported file type", filename)
        return "Unsupported file type", 400
    
    # Respond with the file's content
    return Response(file_obj.read(), content_type=CONTENT_TYPES[ext])

@app.route('/clear_temp', methods=['POST'])
def clear_temp():
    temp_file_path = session.pop('temp_file_path', None)
    session.clear()

    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    return jsonify({"message": "Temp file cleared."})

@app.route('/save', methods=['POST'])
def save_file():
    filename = request.form.get('filename')
    temp_file_path = session.get('temp_file_path')
    
    if not temp_file_path or not os.path.exists(temp_file_path):
        return jsonify({
            "status": "error",
            "message": "Error: Temporary file missing"
        })

    original_extension = os.path.splitext(temp_file_path)[-1]
    if not filename.endswith(original_extension):
        filename += original_extension

    existing_file = mongo.db.fs.files.find_one({"filename": filename})
    if existing_file:
        return jsonify({
            "status": "error",
            "message": "File name already exists, choose another name."
        })

    with open(temp_file_path, 'rb') as f:
        file_id = file_storage.save_file(f, filename)
    
    os.remove(temp_file_path)
    session.pop('temp_file_path', None)
    
    return jsonify({
        "status": "success",
        "message": f"File saved with ID: {file_id}"
    })

@app.route('/create_project', methods=['POST'])
def create_project_route():
    name = request.form.get('projectname')
    file = request.files.get('initialfile')
    filename = file.filename if file else None

    if not name or not file:
        return jsonify({
            "status": "error",
            "message": "Project name or file missing."
        }), 400

    project_id = file_storage.create_project(name, file, filename)
    return jsonify({
        "status": "success",
        "message": f"Project created with ID: {project_id}"
    })

@app.route('/update_project', methods=['POST'])
def update_project():
    data = request.get_json()
    updated_html = data.get('updatedHtml')
    annotations = data.get('annotations')
    # Validate the received data
    if not updated_html:
        return jsonify({"success": False, "error": "Invalid data received"}), 400

    project_id = session.get('project_id')
    filename = session.get('filename').split('.')[0] + '.html'

    # Update the project version with the new HTML content and annotations
    success = file_storage.update_version(project_id, filename, updated_html, annotations)
    
    if success:
        return jsonify({"success": True, "project_id": project_id})
    else:
        return jsonify({"success": False, "error": "Update failed"}), 500

@app.route('/projects', methods=['GET'])
def list_projects():
    projects = file_storage.list_all_projects()
    
    # Convert ObjectId to string for each project
    for project in projects:
        project["_id"] = str(project["_id"])
        
    return jsonify({"projects": projects})

@app.route('/project_versions/<project_id>', methods=['GET'])
def get_versions(project_id):
    session.pop('filename', None)
    session.pop('file_type', None)
    session.pop('file_id', None)
    session['project_id'] = project_id

    # stor e project_id and file_id in session
    versions = file_storage.get_project_versions(project_id)
    
    

    # Convert ObjectId to string for each version's file_id
    for version in versions:
        version["file_id"] = str(version["file_id"])
    return jsonify({"versions": versions})

@app.route('/load_from_mongo', methods=['POST'])
def load_from_mongo():
    file_id = request.form.get('file_id')
    
    if not file_id:
        return jsonify({'error': 'File ID not provided'}), 400

    file_data = file_storage.get_file_by_id(file_id)
    
    if not file_data:
        return jsonify({'error': 'Document not found'}), 404

    # Set the session variables
    session['filename'] = file_data['filename']
    file_type = file_data['filename'].split('.')[-1]
    session['file_type'] = file_type
    session['file_id'] = file_id

    # Save the file temporarily to the server's file system
    temp_file_path = save_temp_file(file_data)
    session['temp_file_path'] = temp_file_path
    # Based on the filetype, determine the action to be taken on the frontend
    ext = '.' + file_type
    if ext == '.html':
        file_data['file_object'].seek(0)  # Resetting file pointer
        content = file_data['file_object'].read().decode("utf-8")
        
        if not content:
            return jsonify({'error': 'Retrieved HTML content is empty'}), 500
        
        annotations = file_data.get('annotations', [])

        return jsonify({
            'filetype': 'html',
            'content': content,
            'annotations': annotations
        })


    elif ext in ['.pdf', '.docx']:
        return jsonify({
            'filetype': file_type,
            'url': url_for('display_file', file_id=str(file_data['file_object']._id))
        })

    return "Unsupported file type", 400

@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_id = request.form.get('file_id')
    if not file_id:
        return jsonify({'success': False, 'error': 'File ID not provided'}), 400
    project_id = session.get('project_id')
    success = file_storage.delete_file(file_id)
    if success:
        return jsonify({'success': True, 'project_id': project_id})
    else:
        return jsonify({'success': False, 'error': 'Failed to delete file'}), 500

@app.route('/delete_project', methods=['POST'])
def delete_project():
    project_id = request.form.get('project_id')
    if not project_id:
        return jsonify({'success': False, 'error': 'Project ID not provided'}), 400

    success = file_storage.delete_project(project_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to delete project'}), 500


# ---------- FILE CONVERSION ROUTE ----------
# route is used to convert the file to html for annotation

@app.route('/annotate', methods=['POST'])
def annotate():
    file_name = session.get('filename')
    temp_file_path = session.get('temp_file_path')

    if not file_name or not file_name.endswith('.pdf'):
        return "No valid PDF filename found in session", 404

    temp_html_file_path = os.path.join(os.path.dirname(temp_file_path), "temp.html")

    # Validate that the file indeed exists
    if not os.path.exists(temp_file_path):
        return f"File {file_name} does not exist on the server", 404

    try:
        subprocess.run(["pdftohtml", "-s", "-noframes", temp_file_path, temp_html_file_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"Conversion failed: {e}", 500

    try:
        with open(temp_html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        return f"Failed to read HTML file: {e}", 500
    finally:
        if os.path.exists(temp_html_file_path):
            os.remove(temp_html_file_path)

    image_dir = os.path.dirname(temp_html_file_path)
    image_refs = re.findall(r'src="([^"]+)"', html_content)

    for img in image_refs:
        img_path = os.path.join(image_dir, img)
        if os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            os.remove(img_path)
            html_content = html_content.replace(f'src="{img}"', f'src="data:image/png;base64,{img_base64}"')

    session['filetype'] = '.html'  # Update the session's filetype to html

    return html_content


# ---------- ATTACK FLOW ROUTES ----------

@app.route('/open_attack_flow')
def open_attack_flow():
    return redirect("http://localhost:8080")


# ---------- Annotation Routes ----------


# ---------- DEBUGGING ----------

@app.route('/clear_database', methods=['POST'])
def clear_database():
    try:
        # Clear the projects collection
        mongo.db.projects.delete_many({})

        # Clear the fs.files collection
        mongo.db.fs.files.delete_many({})

        # Clear the fs.chunks collection
        mongo.db.fs.chunks.delete_many({})

        return jsonify({'success': True, 'message': 'Database cleared successfully!'})
    except Exception as e:
        print(f"Error clearing database: {e}")
        return jsonify({'success': False, 'message': 'Error clearing database.'}), 500

if __name__ == "__main__":
    app.run(debug=True)
