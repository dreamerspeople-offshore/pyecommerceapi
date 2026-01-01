from flask import Flask, jsonify
from flasgger import Swagger
from app.extensions import mongo
from flask_cors import CORS
from app.routes.main_routes import user_bp
from app.routes.product_routes import product_bp
from app.routes.common_routes import common_bp
from app.routes.category_routes import category_bp
from app.routes.fileupload_routes import fileupload_bp
from app.routes.search_routes import search_bp

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object('config.Config')

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    # Initialize MongoDB
    mongo.init_app(app)
    swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}
    Swagger(app, config=swagger_config)
     
    @app.route('/')
    def index():
        return jsonify({"message": "Hello, World!"})

    @app.route('/check_mongo_connection')
    def check_mongo_connection():
        try:
            mongo.cx.admin.command('ping')
            return jsonify({"status": "MongoDB connected successfullyl", "db": mongo.db.name}), 200
        except Exception as e:
            return jsonify({"status": "Failed to connect to MongoDB", "error": str(e)}), 500
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(common_bp, url_prefix='/api/common')
    app.register_blueprint(category_bp, url_prefix='/api/categories')
    app.register_blueprint(fileupload_bp, url_prefix='/api/fileupload')

    return app

# @app.after_request
# def add_cors_headers(response):
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
#     response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
#     return response