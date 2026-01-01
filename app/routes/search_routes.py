from flask import Blueprint, request, jsonify
from app.extensions import mongo
from flasgger import swag_from
search_bp = Blueprint("search_bp", __name__)

@search_bp.route("/api/searchforname", methods=["POST"])
def search_for_name():
    """
    Search dynamically in any collection with pagination and field selection.
    ---
    tags:
      - Search
    summary: "Search in a specified database and collection with optional filtering, pagination, and selected fields"
    description: "Search for records in a MongoDB collection using dynamic filtering, pagination, and case-insensitive search. Allows selecting specific fields to return."
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
              example: "ecommerce_db"
            collection:
              type: string
              example: "products"
            page:
              type: integer
              example: 1
              default: 1
            page_records:
              type: integer
              example: 100
              default: 100
            productName:
              type: string
              example: "Test Product"
            fields:
              type: array
              items:
                type: string
              example: ["productName", "sku", "category"]
              description: "List of fields to return in the response."
    responses:
      200:
        description: "Returns the filtered results with pagination."
        schema:
          type: object
          properties:
            count:
              type: integer
              example: 10
            data:
              type: array
              items:
                type: object
                properties:
                  _id:
                    type: string
                    example: "65a4b32c5a8f77d10c1b2a34"
                  category:
                    type: string
                    example: "fashion"
                  productName:
                    type: string
                    example: "Test Product"
                  sku:
                    type: string
                    example: "1415"
      400:
        description: "Invalid request due to missing required fields."
      500:
        description: "Internal server error."
    """
    try:
        data = request.get_json()
        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()
        page = int(data.get("page", 1))
        page_records = int(data.get("page_records", 1000))
        fields = data.get("fields", [])  # Fields to return

        if not database_name or not collection_name:
            return jsonify({"error": "Database and collection are required"}), 400

        # Check Redis cache before querying MongoDB
        cached_result = get_cached_search_results(data)
        if cached_result:
            return jsonify(cached_result), 200

        # Build query
        query = {k: {"$regex": f"^{v}", "$options": "i"} for k, v in data.items() if v and k not in ["database", "collection", "page", "page_records", "fields"]}

        # Get collection and execute query
        db = mongo.cx[database_name]
        collection = db[collection_name]

        # Define projection (return only requested fields)
        projection = {field: 1 for field in fields} if fields else None

        # Pagination
        skip_records = (page - 1) * page_records
        results = list(collection.find(query, projection).skip(skip_records).limit(page_records))

        for item in results:
            item["_id"] = str(item["_id"])

        response_data = {"count": len(results), "data": results}

        # Cache the result
        cache_search_results(data, response_data)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@search_bp.route("/api/tabledata", methods=["POST"])
def get_table_data():
    """
    Search dynamically in any collection with pagination, field selection, and sorting.
    ---
    tags:
      - Search
    summary: "Search in a specified database and collection with optional filtering, pagination, selected fields, and sorting"
    description: "Search for records in a MongoDB collection using dynamic filtering, pagination, case-insensitive search, and sorting. Allows selecting specific fields to return."
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
            page:
              type: integer
              example: 1
              default: 1
            page_records:
              type: integer
              example: 100
              default: 100
            productName:
              type: string
              example: "Test Product"
            fields:
              type: array
              items:
                type: string
              example: ["productName", "sku", "category"]
              description: "List of fields to return in the response."
            sort_by:
              type: string
              example: "createdAt"
              description: "Field name to sort by."
            direction:
              type: string
              enum: [asc, desc]
              example: "desc"
              description: "Sort direction: 'asc' for ascending, 'desc' for descending."
    responses:
      200:
        description: "Returns the filtered results with pagination."
        schema:
          type: object
          properties:
            count:
              type: integer
              example: 10
            data:
              type: array
              items:
                type: object
                properties:
                  _id:
                    type: string
                    example: "65a4b32c5a8f77d10c1b2a34"
                  category:
                    type: string
                    example: "fashion"
                  productName:
                    type: string
                    example: "Test Product"
                  sku:
                    type: string
                    example: "1415"
      400:
        description: "Invalid request due to missing required fields."
      500:
        description: "Internal server error."
    """
    try:
        data = request.get_json()
        print("Received request data:", data)  # Debug log
        
        # Validate required fields
        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()
        if not database_name or not collection_name:
            return jsonify({"error": "Database and collection are required"}), 400

        # Get parameters with defaults
        page = int(data.get("page", 1))
        page_records = int(data.get("page_records", 10))
        fields = data.get("fields", [])
        sort_data = data.get("sort", {})
        filters = data.get("filters", data)  # Fallback to root level for backward compatibility

        # Build query
        query = {}
        if isinstance(filters, dict):
            print("Raw filters:", filters)  # Debug log
            for key, value in filters.items():
                if key in ["database", "collection", "page", "page_records", "fields", "sort"]:
                    continue
                    
                if isinstance(value, dict):
                    data_type = value.get("data_type", "text")
                    search_value = value.get("search_by")
                    
                    if search_value is None:
                        continue
                        
                    if data_type == "text":
                        query[key] = {"$regex": f".*{search_value}.*", "$options": "i"}
                    elif data_type == "number":
                        try:
                            query[key] = float(search_value) if "." in search_value else int(search_value)
                        except ValueError:
                            continue
                    elif data_type == "exact":
                        query[key] = search_value
                elif value is not None:
                    if isinstance(value, str):
                        query[key] = {"$regex": f".*{value}.*", "$options": "i"}
                    else:
                        query[key] = value

        print("Constructed query:", query)  # Debug log

        # Database operations
        db = mongo.cx[database_name]
        collection = db[collection_name]
        
        # Check if collection exists
        if collection_name not in db.list_collection_names():
            return jsonify({"error": f"Collection {collection_name} not found"}), 404

        # Projection
        projection = {field: 1 for field in fields} if fields else None
        skip_records = (page - 1) * page_records

        # Sorting
        sort_clause = []
        if sort_data.get("sort_by"):
            direction = 1 if sort_data.get("direction", "asc").lower() == "asc" else -1
            sort_clause = [(sort_data["sort_by"], direction)]

        # Execute query
        cursor = collection.find(query, projection)
        if sort_clause:
            cursor = cursor.sort(sort_clause)
            
        results = list(cursor.skip(skip_records).limit(page_records))
        for item in results:
            item["_id"] = str(item["_id"])

        total_count = collection.count_documents(query)
        
        print(f"Found {len(results)} results")  # Debug log
        
        return jsonify({
            "count": total_count,
            "data": results
        }), 200

    except Exception as e:
        print("Error:", str(e))  # Debug log
        return jsonify({"error": str(e)}), 500

