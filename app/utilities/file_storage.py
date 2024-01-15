from gridfs import GridFS
from flask import current_app
from bson import ObjectId
from .. import mongo
from datetime import datetime

def save_file(file, filename, annotations=[]):
    """
    Save a file to GridFS.
    Returns the ObjectId of the saved file.
    """
    fs = GridFS(mongo.db)
    if isinstance(file, str):
        file = file.encode('utf-8')

    file_id = fs.put(file, filename=filename, metadata={'annotations': annotations})
    return file_id

def get_file_by_filename(filename):
    """
    Retrieve a file from GridFS by its filename.
    Returns the file object.
    """
    fs = GridFS(mongo.db)
    return fs.find_one({'filename': filename})

def get_file_by_id(file_id):
    """
    Retrieve a file from GridFS by its ObjectId.
    Returns the file object along with its filename.
    """
    try:
        fs = GridFS(mongo.db)
        if not ObjectId.is_valid(file_id):
            print(f"Invalid ObjectId format: {file_id}")
            return None

        file_obj = fs.find_one({'_id': ObjectId(file_id)})
        if not file_obj:
            print(f"No file found with ObjectId: {file_id}")
            return None

        # Note the changes here:
        metadata = getattr(file_obj, "metadata", {})
        annotations = metadata.get('annotations', [])

        return {
            'file_object': file_obj,
            'filename': file_obj.filename,
            'annotations': annotations
        }

    except Exception as e:
        print(f"Error in get_file_by_id: {str(e)}")
        return None

def delete_file(file_id):
    """
    Delete a file from GridFS by its ObjectId and also remove its reference from the projects collection.
    """
    fs = GridFS(mongo.db)

    # Search directly in the underlying 'fs.files' collection
    file_obj = mongo.db.fs.files.find_one({'_id': ObjectId(file_id)})
    if not file_obj:
        print(f"File with ID {file_id} not found in GridFS.")
        return False

    try:
        fs.delete(ObjectId(file_id)) 
        mongo.db.projects.update_many({}, {"$pull": {"versions": {"file_id": ObjectId(file_id)}}})
        
        print(f"File with ID {file_id} deleted successfully.")
        return True
    except Exception as e:
        print(f"Error deleting file with ID {file_id}: {e}")
        return False

def delete_project(project_id):
    """
    Delete a project from the projects collection and also delete all of its versions from GridFS.
    """
    fs = GridFS(mongo.db)

    # Delete all versions of the project from GridFS
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if project:
        for version in project.get('versions', []):
            fs.delete(version['file_id'])
    
    # Delete the project from the projects collection
    result = mongo.db.projects.delete_one({"_id": ObjectId(project_id)})
    return result.deleted_count > 0

def get_all_documents():
    """
    Return a list of all documents in GridFS.
    """
    fs = GridFS(mongo.db)
    return [{'filename': doc['filename'], 'uploadDate': doc['uploadDate']} for doc in mongo.db.fs.files.find()]


# ---------- PROJECT TABLES ----------
def create_project(project_name, file, filename):
    # Save the file to GridFS first
    file_id = save_file(file, filename)
    
    # Create a new project entry with an initial version
    project_entry = {
        "project_name": project_name,
        "File_name": filename,
        "File_type": filename.split('.')[-1],
        "creation_date": datetime.utcnow(),
        "versions": [{
            "file_id": file_id,
            "version_date": datetime.utcnow()
        }]
    }

    result = mongo.db.projects.insert_one(project_entry)
    return result.inserted_id

def list_all_projects():
    projects_cursor = mongo.db.projects.find({}, {"project_name": 1})  # Only retrieve the project_name and _id
    projects = list(projects_cursor)
    return projects

def get_project_versions(project_id):
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if project:
        return project.get('versions', [])
    return []

def update_version(project_id, filename, updated_html, annotations):
    """
    Adds a new version to a specific project.
    
    :param project_id: The ID of the project to which the version will be added.
    :param file: The file object to save in GridFS.
    :param filename: The name of the file to save.
    :param annotations: The annotations of the file.
    :return: Update result.
    """
    # Save the updated HTML to GridFS
    file_id = save_file(updated_html, filename, annotations)
    
    # Add the new version to the project
    version_entry = {
        "file_id": file_id,
        "version_date": datetime.utcnow()
    }
    
    result = mongo.db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"versions": version_entry}}
    )

    # Check if the update was successful
    return result.modified_count > 0