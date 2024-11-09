import os
from flask import Blueprint, request, jsonify, safe_join
import pyclamd
from app import db
from app.models import Product
import pandas as pd
import magic
from werkzeug.utils import secure_filename

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_all_products():
  products = Product.query.all()
  for product in products:
    products_list = [{"id": product.id,
                      "name": product.name,
                      "description": product.description,
                      "price": product.price,
                      "category": product.category,
                      "specifications": product.specifications,
                      "discount": product.discount}]
  return jsonify(products_list)

@products_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
  product = Product.query.get_or_404(id)
  product_data = {"id": product.id,
                  "name": product.name,
                  "description": product.description,
                  "price": product.price,
                  "category": product.category,
                  "specifications": product.specifications,
                  "discount": product.discount}
  
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IMAGE_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}

def validate_image(file):
  if not ('.' in file.filename and file.filename.rsplit('.',1)[1].lower() in IMAGE_EXTENSIONS):
    return False, "Invalid image extension."
  
  if file.content_type not in IMAGE_MIME_TYPES:
    return False, "Invalid image MIME type."
  
  mime = magic.Magic(mime=True)
  file_mime_type = mime.from_file(file)
  if file_mime_type not in IMAGE_MIME_TYPES:
    return False, "Image file type does not match signature."
  
  MAX_IMAGE_SIZE = 5*1024*1024
  file.seek(0, os.SEEK_END)
  if file.tell()>MAX_IMAGE_SIZE:
    file.seek(0)
    return False, "Image file size exceeds limit."
  file.seek(0)

  cd = pyclamd.ClamdNetworkSocket()
  try:
    result = cd.scan_file(file)
    if result != None:
      return False, "Virus detected."
  except Exception as e:
    return None, "Error scanning file: {e}"

  return True, "Image is valid."

@products_bp.route('/products', methods=['POST'])
def add_product():
  data = request.form
  file = request.files.get('image')
  
  if file:
    isValid, message = validate_image(file)
    if not isValid or isValid == None:
      return jsonify({"error": message}), 400
    
    filename = secure_filename(file.filename)
    image_path = safe_join('static/uploads', filename)
    file.save(image_path)
  else:
    image_path = None

  new_product = Product(name=data['name'],
                        description=data['description'],
                        price=data['price'], 
                        category=data['category'], 
                        image_url=image_path, 
                        specifications=data['specifications'])
  db.session.add(new_product)
  db.session.commit()
  return jsonify({"message": "Product added successfully"}), 201

@products_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
  data=request.json
  product = Product.query.get_or_404(id)

  product.name = data.get('name', product.name)
  product.description = data.get('description', product.description)
  product.price = data.get('price', product.price)
  product.category = data.get('category', product.category)
  product.specifications = data.get('specifications', product.specifications)
  product.discount = data.get('discount', product.discount)

  db.session.commit()
  return jsonify({"message": "Product updated successfully"})

@products_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
  product = Product.query.get_or_404(id)
  db.session.delete(product)
  db.session.commit()
  return jsonify({"message": "Product deleted successfully"})

CSV_EXTENSION = {'csv'}
CSV_MIME_TYPE = {'text/csv'}

def validate_csv(file):
  if not ('.' in file.filename and file.filename.rsplit('.',1)[1].lower() in CSV_EXTENSION):
    return False, "Invalid CSV extension."
  
  if file.content_type not in CSV_MIME_TYPE:
    return False, "Invalid CSV MIME type."
  
  MAX_CSV_SIZE = 10*1024*1024
  file.seek(0, os.SEEK_END)
  if file.tell()>MAX_CSV_SIZE:
    file.seek(0)
    return False, "CSV file size exceeds limit."
  file.seek(0)

  cd = pyclamd.ClamdNetworkSocket()
  try:
    result = cd.scan_file(file)
    if result != None:
      return False, "Virus detected."
  except Exception as e:
    return None, "Error scanning file: {e}"

  return True, "CSV is valid."

@products_bp.route('/products/bulk_upload', methods=['POST'])
def bulk_upload_products():
  file = request.files.get('file')
  if file:
    isValid, message = validate_csv(file)
    if not isValid or isValid == None:
      return jsonify({"error": message}), 400
  else:
    return jsonify({"error": "No CSV file provided"}), 400

  
  df = pd.read_csv(file)
  for _, row in df.iterrows():
    new_product = Product(name=row['name'], 
                          description=row.get('description', ''), 
                          price=row['price'], 
                          category=row['category'], 
                          specifications=row.get('specifications', ''), 
                          discount=row.get('discount', 0.0))
    db.session.add(new_product)

  db.session.commit()
  return jsonify({"message": "Bulk upload successful"}), 201