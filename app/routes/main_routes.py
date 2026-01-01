from flask import Blueprint, jsonify, request
from flasgger import swag_from
from app.extensions import mongo
from bson import ObjectId
from bson.json_util import dumps
import gridfs
from werkzeug.utils import secure_filename

user_bp = Blueprint('user', __name__)

# Route to get all users
@user_bp.route('/api/users', methods=['GET'])
@swag_from({
    "responses": {
        200: {
            "description": "Returns a list of all products",
            "examples": {
                "application/json": [
                    {
                        "_id": "66be04dbdd50a4eb333c42fa",
                        "email": "admin@gmail.com"
                    },
                    {
                        "_id": "66bf809144f31c507f7ff98b",
                        "email": "admin2@gmail.com"
                    },
                ]
            }
        }
    }
})
def get_users():
    users = mongo.db.users.find()
    print(users)
    result = []
    for user in users:
        result.append({
            '_id': str(user['_id']),
            'email': user['email']
        })
    return jsonify(result), 200

# Route to add a new user
@user_bp.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    if not data or not 'name' in data or not 'email' in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    user_id = mongo.db.users.insert_one({
        'name': data['name'],
        'email': data['email']
    }).inserted_id
    return jsonify({'message': 'User added', 'user_id': str(user_id)}), 201

# Route to get a single user by ID
@user_bp.route('/api/users/<id>', methods=['GET'])
def get_user(id):
    user = mongo.db.users.find_one({'_id': ObjectId(id)})
    if user:
        return jsonify({
            '_id': str(user['_id']),
            'email': user['email']
        }), 200
    return jsonify({'error': 'User not found'}), 404

# Route to update a user by ID
@user_bp.route('/api/users/<id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    mongo.db.users.update_one({'_id': ObjectId(id)}, {'$set': data})
    return jsonify({'message': 'User updated'}), 200

# Route to delete a user by ID
@user_bp.route('/api/users/<id>', methods=['DELETE'])
def delete_user(id):
    result = mongo.db.users.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 1:
        return jsonify({'message': 'User deleted'}), 200
    return jsonify({'error': 'User not found'}), 404

@user_bp.route('/api/upload', methods=['POST'])
def upload_file():
    database_name = request.form.get('database')
    collection_name = request.form.get('collection')

    if not database_name or not collection_name:
        return jsonify({"error": "Request must contain 'database' and 'collection' parameters."}), 400

    # Get the file from request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Dynamically select the database and collection
        db = mongo.cx[database_name]
        fs = gridfs.GridFS(db, collection=collection_name)

        # Save file to GridFS with metadata
        filename = secure_filename(file.filename)
        file_id = fs.put(file, filename=filename, content_type=file.content_type)

        return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
   
@user_bp.route('/api/getmdbcollection', methods=['POST'])
def filter_data():
# Parse JSON data from the request body
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Get the database and collection from the JSON body
    database_name = data.get('database')
    collection_name = data.get('collection')

    if not database_name or not collection_name:
        return jsonify({"error": "You must specify both 'database' and 'collection' in the request body."}), 400

    # Dynamically select the database and collection
    db = mongo.cx[database_name]
    collection = db[collection_name]

    # Build query based on request body
    query = {}

    # Example filters: name, age range, created_at date range, and email search
    if 'firstName' in data:
        query['firstName'] = data.get('firstName')

    if 'min_age' in data and 'max_age' in data:
        query['age'] = {
            '$gte': int(data.get('min_age')),
            '$lte': int(data.get('max_age'))
        }

    if 'email' in data:
        query['email'] = {'$regex': data.get('email'), '$options': 'i'}

    if 'start_date' in data and 'end_date' in data:
        query['created_at'] = {
            '$gte': data.get('start_date'),
            '$lte': data.get('end_date')
        }

    try:
        # Fetch documents that match the query
        documents = collection.find(query)
        # Convert documents to list and make them JSON serializable
        result = [json_encoder(doc) for doc in documents]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def json_encoder(doc):
    """Helper function to convert ObjectId and other BSON types to JSON-serializable types."""
    if isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, dict):
        for key, value in doc.items():
            doc[key] = json_encoder(value)
    elif isinstance(doc, list):
        return [json_encoder(item) for item in doc]
    return doc