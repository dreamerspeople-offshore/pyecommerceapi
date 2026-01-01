from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.extensions import mongo
from flask_cors import cross_origin
product_bp = Blueprint("product_bp", __name__)
from flasgger import swag_from
from datetime import datetime

def get_collection():
    """Ensure MongoDB is initialized before accessing the collection."""
    if mongo.db is None:
        raise Exception("MongoDB is not initialized. Check your configuration.")
    return mongo.db.products

# Create Product
@product_bp.route("/create", methods=["POST"])
def create_product():
    """
    Create a new product in the specified MongoDB database and collection.
    ---
    tags:
      - Product
    summary: "Insert a new product document into MongoDB"
    description: "Insert a product document into a specified MongoDB collection. All required fields must be provided."
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
            category:
              type: string
              example: "fashion"
            sku:
              type: string
              example: "1415"
            name:
              type: string
              example: "Test Product"
            description:
              type: string
              example: "This is a test product"
            price:
              type: number
              format: float
              example: 99.99
            status:
              type: string
              example: "active"
            country:
              type: string
              example: "USA"
            productLabel:
              type: string
              example: "Best Seller"
    responses:
      201:
        description: "Product created successfully"
      400:
        description: "Missing or invalid fields"
      500:
        description: "Server error"
    """
    try:
        data = request.get_json()

        # Required metadata
        database_name = data.get("database", "").strip()
        collection_name = data.get("collection", "").strip()

        # Required product fields
        required_fields = ["category", "sku", "productName", "active", "country"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"'{field}' is required"}), 400

        # Document to insert
        product_doc = {
            "category": data["category"],
            "sku": data["sku"],
            "productName": data["productName"],
            "description": data.get("description", ""),
            "active": data["active"],
            "country": data["country"],
            "productLabel": data.get("productLabel"),
            "createdAt": datetime.utcnow()
        }

        # MongoDB insert
        db = mongo.cx[database_name]
        collection = db[collection_name]

        # Check for duplicate SKU
        if collection.find_one({"sku": data["sku"]}):
            return jsonify({"error": "SKU must be unique"}), 400

        insert_result = collection.insert_one(product_doc)
        return jsonify({
            "message": "Product created successfully",
            "inserted_id": str(insert_result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# @product_bp.route("/create", methods=["POST"])
# def create_product():
#     """
#     Create a new product and return the created object.
#     ---
#     tags:
#       - Product
#     parameters:
#       - name: body
#         in: body
#         required: true
#         schema:
#           type: object
#           properties:
#             category:
#               type: string
#             sku:
#               type: string
#             name:
#               type: string
#             description:
#               type: string
#             price:
#               type: number
#             status:
#               type: string
#             country:
#               type: string
#             productLabel:
#               type: string
#             createdAt:
#               type: string
#     responses:
#       201:
#         description: Product created successfully
#       400:
#         description: Validation error
#       500:
#         description: Internal server error
#     """
#     try:
#         # Get MongoDB collection
#         collection = get_collection()

#         # Get request data
#         data = request.json
#         data["createdAt"] = datetime.now()
#         print(data)
#         # Insert into MongoDB
#         product_id = collection.insert_one(data).inserted_id

#         # Retrieve the created product (including ObjectId conversion)
#         created_product = collection.find_one({"_id": product_id})
#         if created_product:
#             created_product["_id"] = str(created_product["_id"])  # Convert ObjectId to string

#         return jsonify({"message": "Product created", "product": created_product}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
# Get All Products
@product_bp.route("/count", methods=["GET"])
def get_productstotalcount():
    """
    Get paginated list of products.
    ---
    tags:
      - Product
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            page:
              type: integer
              default: 0
            page_records:
              type: integer
              default: 100
    responses:
      200:
        description: A list of paginated products
        schema:
          type: object
          properties:
            count:
              type: integer
            products:
              type: array
              items:
                type: object
                properties:
                  _id:
                    type: string
                  category:
                    type: string
                  sku:
                    type: string
                  productName:
                    type: string
                  description:
                    type: string
                  productStatus:
                    type: string
                  country:
                    type: string
                  productLabel:
                    type: string
                  active:
                    type: boolean
    """
    try:
        # Get MongoDB collection
        collection = get_collection()

        # Fetch paginated products
        products = list(collection.find(
            {}, 
            {"_id": 1, "category": 1, "sku": 1, "productName": 1, "description": 1, 
             "productStatus": 1, "country": 1, "productLabel": 1, "active": 1}
        ).sort("_id", -1))

        # Convert ObjectId to string
        for product in products:
            product["_id"] = str(product["_id"])

        return jsonify({"response_count": len(products)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Get All Products
@product_bp.route("/list", methods=["POST"])
def get_products():
    """
    Get paginated list of products with optional field selection.
    ---
    tags:
      - Product
    summary: "Fetch paginated products with optional field selection"
    description: "Returns a paginated list of products. Users can specify which fields to include in the response."
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            page:
              type: integer
              example: 0
              default: 0
            page_records:
              type: integer
              example: 100
              default: 100
            fields:
              type: array
              items:
                type: string
              example: ["productName", "sku", "category"]
              description: "List of fields to return in the response."
    responses:
      200:
        description: "Returns paginated products with selected fields."
        schema:
          type: object
          properties:
            count:
              type: integer
              example: 10
            products:
              type: array
              items:
                type: object
                properties:
                  _id:
                    type: string
                    example: "65a4b32c5a8f77d10c1b2a34"
                  productName:
                    type: string
                    example: "Test Product"
                  sku:
                    type: string
                    example: "1415"
                  category:
                    type: string
                    example: "fashion"
      400:
        description: "Invalid request due to missing required fields."
      500:
        description: "Internal server error."
    """
    try:
        # Parse request JSON body
        data = request.get_json()
        page = int(data.get("page", 0))  # Default to page 0
        page_records = int(data.get("page_records", 100))  # Default to 100 records per page
        fields = data.get("fields", [])  # Fields to return

        # Get MongoDB collection
        collection = get_collection()

        # Pagination: Calculate skip value
        skip_records = page * page_records

        # Implement field selection (always include `_id`)
        if fields:
            projection = {"_id": 1}  # Always include `_id`
            projection.update({field: 1 for field in fields})
        else:
            projection = None  # Fetch all fields
        # Fetch paginated products with selected fields
        products = list(collection.find({}, projection).skip(skip_records).limit(page_records))

        # Convert ObjectId to string
        for product in products:
            product["_id"] = str(product["_id"])

        return jsonify({"count": len(products), "products": products}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Single Product by ID
@product_bp.route("/detail/<string:id>", methods=["GET"])
def get_product(id):
    """
    Retrieve a product by its ID.
    ---
    tags:
      - Product
    parameters:
      - name: id
        in: path
        required: true
        description: The unique ID of the product
        type: string
    responses:
      200:
        description: Returns the product details
      400:
        description: Invalid ID format
      404:
        description: Product not found
    """
    try:
        collection = get_collection()

        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid product ID format"}), 400

        # Query product
        product = collection.find_one({"_id": ObjectId(id)})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        # Convert ObjectId to string
        product["_id"] = str(product["_id"])

        return jsonify(product), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update Product
@product_bp.route("/update/<string:id>", methods=["PUT"])
def update_product(id):
    """
    Update an existing product.
    ---
    tags:
      - Product
    parameters:
      - name: id
        in: path
        required: true
        type: string
        description: The product ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            category:
              type: string
            sku:
              type: string
            name:
              type: string
            description:
              type: string
            price:
              type: number
            status:
              type: string
            country:
              type: string
            productLabel:
              type: string
    responses:
      200:
        description: Product updated successfully
      400:
        description: Validation error or invalid ID
      404:
        description: Product not found
      500:
        description: Internal server error
    """
    try:
        collection = get_collection()

        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid product ID"}), 400

        # Validate request data
        data = request.json
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        # Ensure '_id' is not in the update data
        data.pop("_id", None)

        # Update the product
        result = collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": data},
            return_document=True  # Returns updated document
        )

        # If product not found
        if not result:
            return jsonify({"error": "Product not found"}), 404

        # Convert `_id` to string
        result["_id"] = str(result["_id"])

        return jsonify({"message": "Product updated", "product": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete Product
@product_bp.route("/remove/<string:id>", methods=["DELETE"])
def delete_product(id):
    """
    Delete a product by its ID.
    ---
    tags:
      - Product
    parameters:
      - name: id
        in: path
        required: true
        description: The unique ID of the product to be deleted
        type: string
    responses:
      200:
        description: Product successfully deleted
      400:
        description: Invalid ID format
      404:
        description: Product not found
      500:
        description: Internal server error
    """
    try:
        collection = get_collection()

        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid product ID format"}), 400

        # Delete the product
        result = collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Check unique with category and sku
@product_bp.route("/check-unique", methods=["POST"])
def check_unique_with_category_and_sku():
    """
    Check if a product with the given category and SKU already exists.
    ---
    tags:
      - Product
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            category:
              type: string
            sku:
              type: string
    responses:
      200:
        description: Returns whether the product exists
      400:
        description: Validation error
    """
    try:
        # Validate request body
        data = request.json
        category = data["category"]
        sku = data["sku"]

        # Query MongoDB
        collection = get_collection()
        products = list(collection.find({"category": category, "sku": sku}, {"_id": 1}))

        # Convert _id to string
        for product in products:
            product["_id"] = str(product["_id"])

        return jsonify({"products": products}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@product_bp.route("/unique-column", methods=["GET"])
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
        column_name = request.args.get("column")

        if not column_name:
            return jsonify({"error": "Column name is required"}), 400

        # Get collection
        collection = get_collection()

        # Use MongoDB distinct() to get unique values for the column
        unique_values = collection.distinct(column_name)

        return jsonify({"column": column_name, "values": unique_values}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500