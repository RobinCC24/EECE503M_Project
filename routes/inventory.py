from flask import Blueprint, redirect, render_template, request, jsonify, url_for, flash
from app import db
from models.ecommerce_models import Customer, Order, Product, Category, Subcategory, Inventory, Warehouse

inventory_bp = Blueprint('inventory', __name__)

# Get inventory data and display it
@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    all_inventory = Inventory.query.all()
    inventory_data = []
    for item in all_inventory:
        inventory_data.append({
            "id": item.id,
            "product": item.product.name,
            "warehouse": item.warehouse.location,
            "quantity": item.quantity,
        })
    return render_template('admin/inventory/list.html', inventory=inventory_data)

# Add inventory entry
@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory_entry():
    products = Product.query.all()
    warehouses = Warehouse.query.all()

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        warehouse_id = request.form.get('warehouse_id')
        quantity = request.form.get('quantity')

        # Validate IDs
        if not product_id or not warehouse_id or not quantity:
            flash("All fields are required.", "danger")
            return render_template('admin/inventory/add_inventory.html', products=products, warehouses=warehouses)

        product = Product.query.get(product_id)
        warehouse = Warehouse.query.get(warehouse_id)

        if not product:
            flash("Invalid product selected.", "danger")
            return render_template('admin/inventory/add_inventory.html', products=products, warehouses=warehouses)

        if not warehouse:
            flash("Invalid warehouse selected.", "danger")
            return render_template('admin/inventory/add_inventory.html', products=products, warehouses=warehouses)

        # Check if the inventory already exists
        existing_inventory = Inventory.query.filter_by(product_id=product_id, warehouse_id=warehouse_id).first()
        if existing_inventory:
            existing_inventory.quantity += int(quantity)
        else:
            new_inventory = Inventory(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=quantity
            )
            db.session.add(new_inventory)

        db.session.commit()
        flash("Inventory added successfully.", "success")
        return redirect(url_for('inventory.get_inventory'))

    return render_template('admin/inventory/add_inventory.html', products=products, warehouses=warehouses)

# Update inventory entry
@inventory_bp.route('/inventory/update/<int:inventory_id>', methods=['GET', 'POST'])
def update_inventory(inventory_id):
    inventory_item = Inventory.query.get_or_404(inventory_id)
    products = Product.query.all()
    warehouses = Warehouse.query.all()

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        warehouse_id = request.form.get('warehouse_id')
        quantity = request.form.get('quantity')

        # Validate input
        if not product_id or not warehouse_id or not quantity:
            flash("All fields are required.", "danger")
            return render_template('admin/inventory/update_inventory.html', inventory_item=inventory_item, products=products, warehouses=warehouses)

        product = Product.query.get(product_id)
        warehouse = Warehouse.query.get(warehouse_id)

        if not product:
            flash("Invalid product selected.", "danger")
            return render_template('admin/inventory/update_inventory.html', inventory_item=inventory_item, products=products, warehouses=warehouses)

        if not warehouse:
            flash("Invalid warehouse selected.", "danger")
            return render_template('admin/inventory/update_inventory.html', inventory_item=inventory_item, products=products, warehouses=warehouses)

        try:
            # Update the inventory record
            inventory_item.product_id = int(product_id)
            inventory_item.warehouse_id = int(warehouse_id)
            inventory_item.quantity = int(quantity)

            db.session.commit()
            flash("Inventory updated successfully.", "success")
            return redirect(url_for('inventory.get_inventory'))
        except Exception as e:
            flash(f"Error updating inventory: {e}", "danger")
            db.session.rollback()

    return render_template('admin/inventory/update_inventory.html', inventory_item=inventory_item, products=products, warehouses=warehouses)

# Generate inventory report
@inventory_bp.route('/inventory/report', methods=['GET'])
def generate_report():
    category_report = db.session.query(
        Category.name,
        db.func.sum(Inventory.quantity).label('total_stock')
    ).join(Subcategory).join(Product).join(Inventory).group_by(Category.name).all()

    popular_products = db.session.query(
        Product.name,
        db.func.sum(Inventory.quantity).label('total_stock')
    ).join(Inventory, Inventory.product_id == Product.id).group_by(Product.id).order_by(
        db.func.sum(Inventory.quantity).desc()).limit(5).all()

    report = {
        "category_summary": [{"category": c[0], "total_stock": c[1]} for c in category_report],
        "top_products": [{"product": p[0], "stock": p[1]} for p in popular_products]
    }

    return render_template('admin/inventory/report.html', report=report)

# Manage categories
@inventory_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        data = request.form
        category = Category(name=data['name'])
        db.session.add(category)
        db.session.commit()
        flash("Category added successfully.", "success")
        return redirect(url_for('inventory.get_inventory'))
    return render_template('admin/inventory/add_category.html')

# Manage subcategories
@inventory_bp.route('/subcategories', methods=['GET', 'POST'])
def manage_subcategories():
    categories = Category.query.all()
    if request.method == 'POST':
        data = request.form
        category_id = data.get('category_id')
        subcategory = Subcategory(name=data['name'], category_id=category_id)
        db.session.add(subcategory)
        db.session.commit()
        flash("Subcategory added successfully.", "success")
        return redirect(url_for('inventory.get_inventory'))
    return render_template('admin/inventory/add_subcategory.html', categories=categories)

# Manage warehouses
@inventory_bp.route('/warehouses', methods=['GET', 'POST'])
def manage_warehouses():
    if request.method == 'POST':
        data = request.form
        warehouse = Warehouse(location=data['location'])
        db.session.add(warehouse)
        db.session.commit()
        flash("Warehouse added successfully.", "success")
        return redirect(url_for('inventory.get_inventory'))
    return render_template('admin/inventory/add_warehouse.html')
