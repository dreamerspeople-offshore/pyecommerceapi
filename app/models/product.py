from app.extensions import db
from datetime import datetime

class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    productLabel = db.Column(db.String(100), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
