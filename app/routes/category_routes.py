from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.extensions import mongo


category_bp = Blueprint("category_bp", __name__)

def get_collection():
    """Ensure MongoDB is initialized before accessing the collection."""
    if mongo.db is None:
        raise Exception("MongoDB is not initialized. Check your configuration.")
    return mongo.db.categories

# Create Category
@category_bp.route("/", methods=["POST"])
def create_category():
    collection = get_collection()
    data = request.json
    category_id = collection.insert_one(data).inserted_id
    return jsonify({"message": "Category created", "id": str(category_id)}), 201