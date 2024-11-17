import os
from flask import Blueprint, request, jsonify, redirect, render_template, url_for, flash
from extensions import db
from models.ecommerce_models import Product, Category, Subcategory, Inventory
from werkzeug.utils import secure_filename, safe_join
import pandas as pd
import magic

# Define the product blueprint
product_bp = Blueprint('products', __name__, url_prefix='/api/products')

# Constants for file validation
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IMAGE_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}
CSV_EXTENSION = {'csv'}
CSV_MIME_TYPE = {'text/csv'}

# Utility functions
def validate_image(file):
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS):
        return False, "Invalid image extension."
    if file.content_type not in IMAGE_MIME_TYPES:
        return False, "Invalid image MIME type."
    mime = magic.Magic(mime=True)
    file.seek(0)
    file_mime_type = mime.from_buffer(file.read(1024))
    if file_mime_type not in IMAGE_MIME_TYPES:
        return False, "Image file type does not match signature."
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_IMAGE_SIZE:
        file.seek(0)
        return False, "Image file size exceeds limit."
    file.seek(0)
    return True, "Image is valid."

def validate_csv(file):
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in CSV_EXTENSION):
        return False, "Invalid CSV extension."
    if file.content_type not in CSV_MIME_TYPE:
        return False, "Invalid CSV MIME type."
    MAX_CSV_SIZE = 10 * 1024 * 1024
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_CSV_SIZE:
        file.seek(0)
        return False, "CSV file size exceeds limit."
    file.seek(0)
    return True, "CSV is valid."

# Routes
@product_bp.route('/', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    products_list = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category": product.subcategory.category.name if product.subcategory else None,
            "subcategory": product.subcategory.name if product.subcategory else None,
            "specifications": product.specifications,
            "discount": product.discount,
        }
        for product in products
    ]
    return jsonify({"products": products_list})

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    product_data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.subcategory.category.name if product.subcategory else None,
        "subcategory": product.subcategory.name if product.subcategory else None,
        "specifications": product.specifications,
        "discount": product.discount,
    }
    return jsonify(product_data)

@product_bp.route('/', methods=['POST'])
def add_product():
    data = request.form
    file = request.files.get('image')
    if file:
        is_valid, message = validate_image(file)
        if not is_valid:
            return jsonify({"error": message}), 400
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        file.save(safe_join(upload_dir, filename))
        image_url = os.path.join('static', 'uploads', filename)
    else:
        image_url = None

    subcategory_name = data.get('subcategory_name')
    subcategory = Subcategory.query.filter_by(name=subcategory_name).first()
    if not subcategory:
        return jsonify({"error": "Subcategory not found"}), 400

    new_product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=float(data['price']),
        subcategory_id=subcategory.id,
        image_url=image_url,
        specifications=data.get('specifications', ''),
        discount=float(data.get('discount', 0)),
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully", "product_id": new_product.id})

@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = float(data.get('price', product.price))
    product.specifications = data.get('specifications', product.specifications)
    product.discount = float(data.get('discount', product.discount))

    if 'image' in request.files:
        file = request.files['image']
        is_valid, message = validate_image(file)
        if not is_valid:
            return jsonify({"error": message}), 400
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        file.save(safe_join(upload_dir, filename))
        product.image_url = os.path.join('static', 'uploads', filename)

    db.session.commit()
    return jsonify({"message": "Product updated successfully"})

@product_bp.route('/bulk_upload', methods=['POST'])
def bulk_upload_products():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No CSV file provided"}), 400
    is_valid, message = validate_csv(file)
    if not is_valid:
        return jsonify({"error": message}), 400

    df = pd.read_csv(file)
    required_columns = {'name', 'price', 'subcategory_name'}
    if not required_columns.issubset(df.columns):
        return jsonify({"error": "Missing required columns in CSV"}), 400

    for _, row in df.iterrows():
        subcategory = Subcategory.query.filter_by(name=row['subcategory_name']).first()
        if not subcategory:
            continue
        new_product = Product(
            name=row['name'],
            price=row['price'],
            subcategory_id=subcategory.id,
            description=row.get('description', ''),
            specifications=row.get('specifications', ''),
            discount=row.get('discount', 0),
        )
        db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Bulk upload completed successfully"})
