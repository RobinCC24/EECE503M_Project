from flask import Blueprint, redirect, render_template, request, jsonify, url_for
from app import db
from app.models import Category, Product, Inventory, Subcategory, Warehouse

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
  all_inventory = Inventory.query.all()
  products = Product.query.all()
  warehouses = Warehouse.query.all()
  inventory_data = []
  for item in all_inventory:
    inventory_data.append({"product": item.product.name,
                           "warehouse": item.warehouse.location,
                           "quantity": item.quantity})
  return render_template('inventory.html',products=products, warehouses=warehouses, inventory_data=inventory_data)

@inventory_bp.route('/inventory/filter', methods=['GET'])
def filter_inventory():
    product_id = request.args.get('product_id')
    warehouse_id = request.args.get('warehouse_id')

    query = Inventory.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    filtered_inventory = query.all()
    filtered_data = []
    for item in filtered_inventory:
        filtered_data.append({
            "product": item.product.name,
            "warehouse": item.warehouse.location,
            "quantity": item.quantity
        })
    
    return jsonify({"inventory": filtered_data})

@inventory_bp.route('/inventory/add', methods=['GET'])
def add_inventory_form():
  products = Product.query.all()  
  warehouses = Warehouse.query.all()

  return render_template('add_inventory.html', products=products, warehouses=warehouses)


@inventory_bp.route('/inventory/add', methods=['POST'])
def add_inventory_entry():
  data = request.form
  product_id = data['product_id']
  warehouse_id = data['warehouse_id']
  quantity = data['quantity']

  product = Product.query.get(product_id)
  warehouse = Warehouse.query.get(warehouse_id)
  if not product or not warehouse:
    return jsonify({"error": "Invalid product or warehouse ID"}), 400
  
  existing_inventory = Inventory.query.filter_by(product_id=product_id, warehouse_id=warehouse_id).first()
  if existing_inventory:
   quantity = int(data['quantity'])
   existing_inventory.quantity += quantity
   db.session.commit()
   return redirect(url_for('inventory.get_inventory')) 
  
  new_inventory = Inventory(product_id=product_id, warehouse_id=warehouse_id, quantity=quantity)
  db.session.add(new_inventory)
  db.session.commit()

  return redirect(url_for('inventory.get_inventory')) 

"""@inventory_bp.route('/inventory/<int:product_id>/<int:warehouse_id>/update', methods=['PUT'])
def update_inventory(product_id, warehouse_id):
  data = request.form
  quantity_change = data.get('quantity_change')
  inventory = Inventory.query.filter_by(product_id=product_id, warehouse_id=warehouse_id).first()

  if inventory:
    quantity_change = int(data['quantity_change'])
    inventory.quantity += quantity_change
    db.session.commit()

    if inventory.quantity<5:
      return jsonify({"alert": f"Low stock alert for {inventory.product.name} in {inventory.warehouse.location}!"})
    
    return jsonify({"message": "Inventory updated successfully"})
  return jsonify({"error": "Inventory record not found"})"""

@inventory_bp.route('/inventory/report', methods=['GET'])
def generate_report():
  category_report = db.session.query(Category.name, db.func.sum(Inventory.quantity).label('total_stock')).join(Subcategory).join(Product).join(Inventory).group_by(Category.name).all()
  popular_products = db.session.query(Product.name, db.func.sum(Inventory.quantity).label('total_stock')).join(Inventory, Inventory.product_id == Product.id).group_by(Product.id).order_by(db.func.sum(Inventory.quantity).desc()).limit(5).all()

  report = {"category_summary": [{"category": c.name, "total_stock": c.total_stock} for c in category_report],
            "top_products": [{"product": p.name, "stock": p.total_stock} for p in popular_products]}
  
  return render_template('report.html', report=report)

@inventory_bp.route('/categories', methods=['GET'])
def show_add_category_form():
    return render_template('add_category.html')

@inventory_bp.route('/categories', methods=['POST'])
def add_category():
  data = request.form
  category = Category(name=data['name'])
  db.session.add(category)
  db.session.commit()
  return redirect(url_for('inventory.get_inventory'))

@inventory_bp.route('/subcategories', methods=['GET'])
def show_add_subcategory_form():
    categories = Category.query.all() 
    return render_template('add_subcategory.html', categories=categories)

@inventory_bp.route('/subcategories', methods=['POST'])
def add_subcategory():
  data = request.form
  category_name = data['category_name']

  category = Category.query.filter_by(name=category_name).first()
  if not category:
      return jsonify({"error": "Category not found"}), 404
  
  subcategory = Subcategory(name=data['name'], category_id=category.id)
  db.session.add(subcategory)
  db.session.commit()
  return redirect(url_for('inventory.get_inventory'))

@inventory_bp.route('/warehouses', methods=['GET'])
def show_add_warehouse_form():
    return render_template('add_warehouse.html')

@inventory_bp.route('/warehouses', methods=['POST'])
def create_warehouse():
    data = request.form
    warehouse = Warehouse(location=data['location'])
    db.session.add(warehouse)
    db.session.commit()
    return redirect(url_for('inventory.get_inventory'))

@inventory_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
def get_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    return jsonify({"id": warehouse.id, "location": warehouse.location})

@inventory_bp.route('/warehouses', methods=['GET'])
def get_all_warehouses():
    warehouses = Warehouse.query.all()
    warehouse_list = [{"id": w.id, "location": w.location} for w in warehouses]
    return jsonify(warehouse_list)

@inventory_bp.route('/warehouses/<int:warehouse_id>', methods=['PUT'])
def update_warehouse(warehouse_id):
    data = request.json
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    warehouse.name = data.get('location', warehouse.location)
    db.session.commit()
    return jsonify({"message": "Warehouse updated successfully"})

@inventory_bp.route('/warehouses/<int:warehouse_id>', methods=['DELETE'])
def delete_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    db.session.delete(warehouse)
    db.session.commit()
    return jsonify({"message": "Warehouse deleted successfully"})

