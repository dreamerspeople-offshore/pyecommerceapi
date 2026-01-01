import re
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.extensions import mongo
from flask_cors import cross_origin
common_bp = Blueprint("common_bp", __name__)
from flasgger import swag_from
from datetime import datetime
from pymongo import UpdateOne
def get_collection():
    """Ensure MongoDB is initialized before accessing the collection."""
    if mongo.db is None:
        raise Exception("MongoDB is not initialized. Check your configuration.")
    return mongo.db.commons
def get_collection_product():
    """Ensure MongoDB is initialized before accessing the collection."""
    if mongo.db is None:
        raise Exception("MongoDB is not initialized. Check your configuration.")
    return mongo.db.products
def get_collection_column():
    """Ensure MongoDB is initialized before accessing the collection."""
    if mongo.db is None:
        raise Exception("MongoDB is not initialized. Check your configuration.")
    return mongo.db.columns_config

# Create common
@common_bp.route("/create", methods=["POST"])
def dynamic_insert():
    """
    Insert a document with dynamic fields into a frontend-specified MongoDB collection.
    ---
    tags:
      - Common
    summary: "Insert a document with dynamic fields"
    description: "Insert a document with any fields into a MongoDB collection specified by the client."
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            database:
              type: string
              example: "ecommercedb"
            collection:
              type: string
              example: "products"
            0:
              type: object
              example: {"fieldName": "name", "fieldValue": "value", "fieldType": "text"}
    responses:
      201:
        description: "Document inserted successfully"
      400:
        description: "Missing required fields"
      500:
        description: "Server error"
    """
    try:
        data = request.get_json()

        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()

        if not database_name or not collection_name:
            return jsonify({"error": "Both 'database' and 'collection' are required"}), 400

        # Build dynamic document by extracting numbered keys
        document = {}
        for key, value in data.items():
            if re.match(r'^\d+$', key):  # check if key is a number
                field_info = value
                field_name = field_info.get("fieldName")
                field_value = field_info.get("fieldValue")
                if field_name:
                    document[field_name] = field_value

        # Optionally add createdAt
        document["createdAt"] = datetime.utcnow()

        # Insert into MongoDB
        db = mongo.cx[database_name]
        collection = db[collection_name]
        result = collection.insert_one(document)

        return jsonify({
            "message": "Document inserted successfully",
            "inserted_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@common_bp.route("/update", methods=["PUT"])
def dynamic_update():
    """
    Update a document with dynamic fields in a MongoDB collection.
    ---
    tags:
      - Common
    summary: "Update a document by _id with dynamic fields"
    description: "Update a document using _id and dynamic fields in a collection specified by the frontend."
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            database:
              type: string
              example: "ecommercedb"
            collection:
              type: string
              example: "products"
            _id:
              type: string
              example: "65a4b32c5a8f77d10c1b2a34"
            any_field:
              type: string
              example: "new value"
    responses:
      200:
        description: "Document updated successfully"
      400:
        description: "Missing required fields"
      404:
        description: "Document not found"
      500:
        description: "Server error"
    """
    try:
        data = request.get_json()

        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()
        doc_id = data.get("_id", "").strip()

        if not database_name or not collection_name or not doc_id:
            return jsonify({"error": "Database, collection, and _id are required"}), 400

        update_fields = {
            k: v for k, v in data.items()
            if k not in ["database", "collection", "_id"]
        }

        db = mongo.cx[database_name]
        collection = db[collection_name]

        result = collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Document not found"}), 404

        # Create a serializable response with the update result details
        response_data = {
            "message": "Document updated successfully",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(doc_id) if doc_id else None
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@common_bp.route("/delete", methods=["DELETE"])
def dynamic_delete():
    """
    Delete a document by _id from a MongoDB collection.
    ---
    tags:
      - Common
    summary: "Delete a document by _id"
    description: "Delete a document using _id in a collection specified by the frontend."
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            database:
              type: string
              example: "ecommercedb"
            collection:
              type: string
              example: "products"
            _id:
              type: string
              example: "65a4b32c5a8f77d10c1b2a34"
    responses:
      200:
        description: "Document deleted successfully"
      400:
        description: "Missing required fields"
      404:
        description: "Document not found"
      500:
        description: "Server error"
    """
    try:
        data = request.get_json()

        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()
        doc_id = data.get("_id", "").strip()

        if not database_name or not collection_name or not doc_id:
            return jsonify({"error": "Database, collection, and _id are required"}), 400

        db = mongo.cx[database_name]
        collection = db[collection_name]

        result = collection.delete_one({"_id": ObjectId(doc_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Document not found"}), 404

        return jsonify({"message": "Document deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@common_bp.route("/unique-column-all", methods=["GET"])
def get_unique_column_values():
    """
    Get unique values for a specified column in the products collection.
    ---
    tags:
      - Product
    parameters:
      - name: column
        in: query
        type: string
        required: true
        description: The column name to get unique values for.
    responses:
      200:
        description: List of unique values for the given column.
      400:
        description: Bad request (e.g., missing column parameter).
      500:
        description: Internal server error.
    """
    try:
        # Get column name from query parameters
        column_name = 'category'

        if not column_name:
            return jsonify({"error": "Column name is required"}), 400

        # Get collection
        collection = get_collection_product()

        # Use MongoDB distinct() to get unique values for the column
        unique_values = collection.distinct(column_name)

        return jsonify({"column": column_name, "values": unique_values}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# GET all column configs
@common_bp.route("/column-configs", methods=["GET"])
@swag_from({
    'tags': ['Column Configs'],
    'responses': {
        200: {
            'description': 'List of all column configurations',
            'examples': {
                'application/json': [
                    {"columnName": "category", "isActive": True},
                    {"columnName": "category1", "isActive": False}
                ]
            }
        },
        500: {'description': 'Internal Server Error'}
    }
})
def get_all_column_configs():
    try:
        collection = get_collection_column()
        configs = list(collection.find({}, {"_id": 0}))
        return jsonify(configs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Single update
@common_bp.route("/column-configs/update", methods=["POST"])
@swag_from({
    'tags': ['Column Configs'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'columnName': {'type': 'string'},
                    'isActive': {'type': 'boolean'}
                },
                'required': ['columnName', 'isActive']
            }
        }
    ],
    'responses': {
        200: {'description': 'Update successful'},
        400: {'description': 'Bad Request'},
        404: {'description': 'Column not found'},
        500: {'description': 'Internal Server Error'}
    }
})
def update_column_is_active():
    try:
        data = request.get_json()
        column_name = data.get("columnName")
        is_active = data.get("isActive")

        if column_name is None or is_active is None:
            return jsonify({"error": "columnName and isActive are required"}), 400

        result = column_collection.update_one(
            {"columnName": column_name},
            {"$set": {"isActive": is_active}}
        )

        if result.matched_count == 0:
            return jsonify({"message": "Column not found"}), 404

        return jsonify({"message": "Update successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Bulk update

@common_bp.route("/column-configs/bulk-update", methods=["POST"])
def bulk_update_column_configs():
    """
    Bulk update the isActive status of columns.

    ---
    tags:
      - Column Configs
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: array
            items:
              type: object
              properties:
                columnName:
                  type: string
                  example: "category"
                isActive:
                  type: boolean
                  example: true
    responses:
      200:
        description: Bulk update result
        content:
          application/json:
            example:
              matched_count: 2
              modified_count: 2
      400:
        description: Invalid input
      500:
        description: Internal Server Error
    """
    try:
        updates = request.get_json()

        if not isinstance(updates, list) or not updates:
            return jsonify({"error": "Payload must be a non-empty array"}), 400

        # Prepare bulk operations
        bulk_ops = []
        for item in updates:
            column_name = item.get("columnName")
            is_active = item.get("isActive")

            if column_name is None or is_active is None:
                return jsonify({"error": "Each item must include 'columnName' and 'isActive'"}), 400

            bulk_ops.append(
                UpdateOne(
                    {"columnName": column_name},
                    {"$set": {"isActive": is_active}},
                    upsert=False
                )
            )

        # Execute bulk update
        result = get_collection_column().bulk_write(bulk_ops)

        return jsonify({
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500