import os
from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
import pyclamd
from app import db
from app.models import Category, Inventory, Product, Subcategory
import pandas as pd
import magic
from werkzeug.utils import secure_filename, safe_join

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_all_products():
  products = Product.query.all()
  categories = Category.query.all()
  subcategories = Subcategory.query.all()
  products_list = []
  for product in products:
    products_list.append({"id": product.id,
                      "name": product.name,
                      "description": product.description,
                      "price": product.price,
                      "category": product.subcategory.category.name,
                      "subcategory": product.subcategory.name,
                      "specifications": product.specifications,
                      "discount": product.discount})
    
  return render_template('products.html', products=products_list, categories=categories, subcategories=subcategories)

@products_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
  product = Product.query.get_or_404(id)
  product_data = {"id": product.id,
                  "name": product.name,
                  "description": product.description,
                  "price": product.price,
                  "category": product.subcategory.category.name,
                  "subcategory": product.subcategory.name,
                  "specifications": product.specifications,
                  "discount": product.discount}
  return render_template('product_detail.html', product=product)
  
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IMAGE_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}

def validate_image(file):
  if not ('.' in file.filename and file.filename.rsplit('.',1)[1].lower() in IMAGE_EXTENSIONS):
    return False, "Invalid image extension."
  
  if file.content_type not in IMAGE_MIME_TYPES:
    return False, "Invalid image MIME type."
  
  mime = magic.Magic(mime=True)
  #file_mime_type = mime.from_file(file)
  file.seek(0)
  file_mime_type = mime.from_buffer(file.read(1024))
  if file_mime_type not in IMAGE_MIME_TYPES:
    return False, "Image file type does not match signature."
  
  MAX_IMAGE_SIZE = 5*1024*1024
  file.seek(0, os.SEEK_END)
  if file.tell()>MAX_IMAGE_SIZE:
    file.seek(0)
    return False, "Image file size exceeds limit."
  file.seek(0)

  """cd = pyclamd.ClamdNetworkSocket()
  try:
    result = cd.scan_file(file)
    if result != None:
      return False, "Virus detected."
  except Exception as e:
    return None, "Error scanning file: {e}"""

  return True, "Image is valid."

@products_bp.route('/products/add', methods=['GET'])
def add_product_form():
    subcategories = Subcategory.query.all()  # Fetch subcategories for the dropdown
    return render_template('add_product.html', subcategories=subcategories)

@products_bp.route('/products', methods=['POST'])
def add_product():
  data = request.form
  file = request.files.get('image')
  
  if file:
    isValid, message = validate_image(file)
    if not isValid or isValid == None:
      return jsonify({"error": message}), 400
    
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    #image_path = safe_join('E:/Fall2024/EECE503M/project/app/static/uploads', filename)
    image_path = safe_join(os.path.join(upload_dir), filename)

    if not os.path.exists(os.path.dirname(image_path)):
            os.makedirs(os.path.dirname(image_path))

    file.save(image_path)
  else:
    image_path = None

  subcategory_name = data.get('subcategory_name')
  subcategory = Subcategory.query.filter_by(name=subcategory_name).first()
  if not subcategory:
        return jsonify({"error": f"Subcategory '{subcategory_name}' not found"}), 400
    
  new_product = Product(name=data['name'],
                        description=data['description'],
                        price=data['price'], 
                        subcategory_id=subcategory.id, 
                        image_url=image_path, 
                        specifications=data['specifications'])
  db.session.add(new_product)
  db.session.commit()
  return redirect(url_for('products.get_all_products'))

@products_bp.route('/products/<int:id>/edit', methods=['GET'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    subcategories = Subcategory.query.all()
    return render_template('update_product.html', product=product, subcategories=subcategories)

@products_bp.route('/products/<int:id>', methods=['POST'])
def update_product(id):
  product = Product.query.get_or_404(id)

  name = request.form.get('name', product.name)
  description = request.form.get('description', product.description)
  price = request.form.get('price', product.price)
  subcategory_name = request.form.get('subcategory_name')
  specifications = request.form.get('specifications', product.specifications)
  discount = request.form.get('discount', product.discount)

  if subcategory_name:
        subcategory = Subcategory.query.filter_by(name=subcategory_name).first()
        if not subcategory:
            return jsonify({"error": f"Subcategory '{subcategory_name}' not found"}), 400
        product.subcategory_id = subcategory.id

  product.name = name
  product.description = description
  product.price = price
  product.specifications = specifications
  product.discount = discount

  if 'image' in request.files:
      image = request.files['image']
      if image.filename != '':
          is_valid, message = validate_image(image)
          if not is_valid:
              return jsonify({"error": message}), 400

          filename = secure_filename(image.filename)
          upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
          image_path = safe_join(os.path.join(upload_dir), filename)

          if not os.path.exists(os.path.dirname(image_path)):
            os.makedirs(os.path.dirname(image_path))

          image.save(image_path)
          product.image_url = filename

  db.session.commit()

  return redirect(url_for('products.get_all_products'))

@products_bp.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if request.form.get('_method') == 'DELETE':
        product = Product.query.get_or_404(id)
        Inventory.query.filter_by(product_id=id).delete()
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('products.get_all_products')) 
    return jsonify({"error": "Invalid request method"}), 405

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

  """""cd = pyclamd.ClamdNetworkSocket()
  try:
    result = cd.scan_file(file)
    if result != None:
      return False, "Virus detected."
  except Exception as e:
    return None, "Error scanning file: {e}"""""

  return True, "CSV is valid."

@products_bp.route('/products/bulk_upload', methods=['GET'])
def bulk_upload_form():
    return render_template('bulk_upload.html')

@products_bp.route('/products/bulk_upload', methods=['POST'])
def bulk_upload_products():
    file = request.files.get('file')
    if file:
      isValid, message = validate_csv(file)
      if not isValid or isValid is None:
          flash(f"Error: {message}", "error")
          return redirect(url_for('products.bulk_upload_form'))
    else:
      flash("Error: No CSV file provided.", "error")
      return redirect(url_for('products.bulk_upload_form'))

    try:
      df = pd.read_csv(file)
      required_columns = {'name', 'price', 'subcategory_name'}
      if not required_columns.issubset(df.columns):
          missing_columns = required_columns - set(df.columns)
          flash(f"Error: Missing required columns: {', '.join(missing_columns)}", "error")
          return redirect(url_for('products.bulk_upload_form'))

      invalid_rows = []
      for index, row in df.iterrows():
        try:
          if not row.get('name') or not row.get('subcategory_name'):
            raise ValueError("Missing required data (name or subcategory_name)")
          if pd.isna(row['name']) or not str(row['name']).strip():
            raise ValueError("Product name cannot be empty")
          price = row.get('price')
          if pd.isnull(price) or not isinstance(price, (int, float)) or price < 0:
            raise ValueError("Invalid price")
          discount = row.get('discount', 0.0)
          if not isinstance(discount, (int, float)) or discount < 0 or discount > 100:
            raise ValueError("Invalid discount (should be between 0 and 100)")
          subcategory_name = row['subcategory_name']
          subcategory = Subcategory.query.filter_by(name=subcategory_name).first()
          if not subcategory:
            raise ValueError(f"Subcategory '{subcategory_name}' does not exist")
          name = row['name']
          new_product = Product(
                name=row['name'],
                description=row.get('description', ''),
                price=price,
                subcategory_id=subcategory.id,
                specifications=row.get('specifications', ''),
                discount=discount
            )
          db.session.add(new_product)
        except ValueError as e:
          invalid_rows.append(f"Row {index + 1}: {str(e)}")
          if invalid_rows:
            for error in invalid_rows:
              flash(error, "error")
            return redirect(url_for('products.bulk_upload_form'))

      try:
        db.session.commit()
      except Exception as e:
        db.session.rollback()
        flash(f"Database error: {e}", 'error')
        return redirect(url_for('products.bulk_upload_form'))
      
      return redirect(url_for('products.get_all_products'))

    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(url_for('products.bulk_upload_form'))

@products_bp.route('/products/filter', methods=['GET'])
def filter_products():
    category_id = request.args.get('category_id')
    subcategory_id = request.args.get('subcategory_id')

    query = Product.query
    if category_id:
        query = query.join(Subcategory).filter(Subcategory.category_id == category_id)
    if subcategory_id:
        query = Product.query.filter_by(subcategory_id=subcategory_id)

    filtered_products = query.all()

    filtered_data = []
    for product in filtered_products:
        filtered_data.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category": product.subcategory.category.name,
            "subcategory": product.subcategory.name,
            "specifications": product.specifications,
            "discount": product.discount
        })

    return jsonify({"products": filtered_data})

