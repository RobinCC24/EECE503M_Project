# admin_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import pandas as pd
from models import db, AdminUser, Role, Permission, Product, Category, Subcategory, Inventory, Order, Customer, Return, Promotion, ActivityLog
from forms.admin_forms import LoginForm, ProductForm, InventoryForm, OrderForm, ReturnForm, BulkUploadForm, PromotionForm
from extensions import login_manager
from datetime import datetime
from utils.utils import validate_csv  # Assume you have validate_csv in utils.py
from forms.admin_forms import EditUserForm 
# Create the admin blueprint
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

# Permission required decorator
def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.has_permission(permission_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Admin login route
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = AdminUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin/login.html', form=form)

# Admin dashboard route
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

# Product Management Routes
@admin_bp.route('/products')
@login_required
@permission_required('manage_products')
def list_products():
    products = Product.query.all()
    return render_template('admin/products/list.html', products=products)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_products')
def create_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.subcategory_id.choices = [(s.id, s.name) for s in Subcategory.query.all()]
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            subcategory_id=form.subcategory_id.data,
            specifications=form.specifications.data,
            discount=form.discount.data
        )
        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join('static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            image_path = os.path.join(upload_dir, filename)
            image_file.save(image_path)
            product.image_url = image_path
        db.session.add(product)
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Created product '{product.name}' (ID: {product.id})"
        )
        db.session.add(log)
        db.session.commit()
        flash('Product created successfully.', 'success')
        return redirect(url_for('admin.list_products'))
    return render_template('admin/products/create.html', form=form)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_products')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.subcategory_id.choices = [(s.id, s.name) for s in Subcategory.query.all()]
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.subcategory_id = form.subcategory_id.data
        product.specifications = form.specifications.data
        product.discount = form.discount.data
        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join('static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            image_path = os.path.join(upload_dir, filename)
            image_file.save(image_path)
            product.image_url = image_path
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Edited product '{product.name}' (ID: {product.id})"
        )
        db.session.add(log)
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin.list_products'))
    return render_template('admin/products/edit.html', form=form, product=product)

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@permission_required('manage_products')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    # Log activity
    log = ActivityLog(
        admin_user_id=current_user.id,
        action=f"Deleted product '{product.name}' (ID: {product.id})"
    )
    db.session.add(log)
    db.session.commit()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin.list_products'))

@admin_bp.route('/products/bulk_upload', methods=['GET', 'POST'])
@login_required
@permission_required('manage_products')
def bulk_upload_products():
    form = BulkUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        is_valid, message = validate_csv(file)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('admin.bulk_upload_products'))
        df = pd.read_csv(file)
        required_columns = {'name', 'price', 'subcategory_name'}
        if not required_columns.issubset(df.columns):
            flash('Missing required columns in CSV', 'danger')
            return redirect(url_for('admin.bulk_upload_products'))
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
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Bulk uploaded products"
        )
        db.session.add(log)
        db.session.commit()
        flash('Bulk upload completed successfully.', 'success')
        return redirect(url_for('admin.list_products'))
    return render_template('admin/products/bulk_upload.html', form=form)

# Inventory Management Routes
@admin_bp.route('/inventory')
@login_required
@permission_required('manage_inventory')
def view_inventory():
    inventory_items = Inventory.query.all()
    return render_template('admin/inventory/list.html', inventory=inventory_items)

@admin_bp.route('/inventory/update/<int:inventory_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_inventory')
def update_inventory(inventory_id):
    inventory_item = Inventory.query.get_or_404(inventory_id)
    form = InventoryForm(obj=inventory_item)
    if form.validate_on_submit():
        inventory_item.quantity = form.quantity.data
        db.session.commit()
        # Check for low stock
        LOW_STOCK_THRESHOLD = 5  # Define your threshold
        if inventory_item.quantity < LOW_STOCK_THRESHOLD:
            flash(f'Low stock alert: {inventory_item.product.name} in {inventory_item.warehouse.location} has low stock ({inventory_item.quantity}).', 'warning')
        else:
            flash('Inventory updated successfully.', 'success')
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Updated inventory for product '{inventory_item.product.name}' in warehouse '{inventory_item.warehouse.location}'"
        )
        db.session.add(log)
        db.session.commit()
        return redirect(url_for('admin.view_inventory'))
    return render_template('admin/inventory/update.html', form=form, inventory_item=inventory_item)

@admin_bp.route('/inventory/report')
@login_required
@permission_required('manage_inventory')
def inventory_report():
    report_data = db.session.query(
        Product.name, db.func.sum(Inventory.quantity).label('total_quantity')
    ).join(Inventory).group_by(Product.id).all()
    return render_template('admin/inventory/report.html', report_data=report_data)

# Order Management Routes
@admin_bp.route('/orders')
@login_required
@permission_required('manage_orders')
def list_orders():
    orders = Order.query.all()
    return render_template('admin/orders/list.html', orders=orders)

@admin_bp.route('/orders/view/<int:order_id>')
@login_required
@permission_required('manage_orders')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/view.html', order=order)

@admin_bp.route('/orders/update/<int:order_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_orders')
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrderForm(obj=order)
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Updated order ID {order.id} status to '{order.status}'"
        )
        db.session.add(log)
        db.session.commit()
        flash('Order updated successfully.', 'success')
        return redirect(url_for('admin.list_orders'))
    return render_template('admin/orders/update.html', form=form, order=order)

@admin_bp.route('/orders/delete/<int:order_id>', methods=['POST'])
@login_required
@permission_required('manage_orders')
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    # Log activity
    log = ActivityLog(
        admin_user_id=current_user.id,
        action=f"Deleted order ID {order.id}"
    )
    db.session.add(log)
    db.session.commit()
    flash('Order deleted successfully.', 'success')
    return redirect(url_for('admin.list_orders'))

# Returns Management Routes
@admin_bp.route('/returns')
@login_required
@permission_required('manage_returns')
def list_returns():
    returns = Return.query.all()
    return render_template('admin/returns/list.html', returns=returns)

@admin_bp.route('/returns/view/<int:return_id>')
@login_required
@permission_required('manage_returns')
def view_return(return_id):
    return_item = Return.query.get_or_404(return_id)
    return render_template('admin/returns/view.html', return_item=return_item)

@admin_bp.route('/returns/update/<int:return_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_returns')
def update_return(return_id):
    return_item = Return.query.get_or_404(return_id)
    form = ReturnForm(obj=return_item)
    if form.validate_on_submit():
        return_item.status = form.status.data
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Updated return ID {return_item.id} status to '{return_item.status}'"
        )
        db.session.add(log)
        db.session.commit()
        flash('Return status updated successfully.', 'success')
        return redirect(url_for('admin.list_returns'))
    return render_template('admin/returns/update.html', form=form, return_item=return_item)

# Promotion Management Routes
@admin_bp.route('/promotions')
@login_required
@permission_required('manage_promotions')
def list_promotions():
    promotions = Promotion.query.all()
    return render_template('admin/promotions/list.html', promotions=promotions)

@admin_bp.route('/promotions/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_promotions')
def create_promotion():
    form = PromotionForm()
    form.product_ids.choices = [(p.id, p.name) for p in Product.query.all()]
    if form.validate_on_submit():
        promotion = Promotion(
            name=form.name.data,
            discount_percent=form.discount_percent.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            user_tier=form.user_tier.data
        )
        promotion.products = Product.query.filter(Product.id.in_(form.product_ids.data)).all()
        db.session.add(promotion)
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Created promotion '{promotion.name}' (ID: {promotion.id})"
        )
        db.session.add(log)
        db.session.commit()
        flash('Promotion created successfully.', 'success')
        return redirect(url_for('admin.list_promotions'))
    return render_template('admin/promotions/create.html', form=form)

@admin_bp.route('/promotions/edit/<int:promotion_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_promotions')
def edit_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    form = PromotionForm(obj=promotion)
    form.product_ids.choices = [(p.id, p.name) for p in Product.query.all()]
    if form.validate_on_submit():
        promotion.name = form.name.data
        promotion.discount_percent = form.discount_percent.data
        promotion.start_date = form.start_date.data
        promotion.end_date = form.end_date.data
        promotion.user_tier = form.user_tier.data
        promotion.products = Product.query.filter(Product.id.in_(form.product_ids.data)).all()
        db.session.commit()
        # Log activity
        log = ActivityLog(
            admin_user_id=current_user.id,
            action=f"Updated promotion '{promotion.name}' (ID: {promotion.id})"
        )
        db.session.add(log)
        db.session.commit()
        flash('Promotion updated successfully.', 'success')
        return redirect(url_for('admin.list_promotions'))
    return render_template('admin/promotions/edit.html', form=form, promotion=promotion)

@admin_bp.route('/promotions/delete/<int:promotion_id>', methods=['POST'])
@login_required
@permission_required('manage_promotions')
def delete_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    db.session.delete(promotion)
    db.session.commit()
    # Log activity
    log = ActivityLog(
        admin_user_id=current_user.id,
        action=f"Deleted promotion '{promotion.name}' (ID: {promotion.id})"
    )
    db.session.add(log)
    db.session.commit()
    flash('Promotion deleted successfully.', 'success')
    return redirect(url_for('admin.list_promotions'))

# Customer Management Routes
@admin_bp.route('/customers')
@login_required
@permission_required('manage_customers')
def list_customers():
    customers = Customer.query.all()
    return render_template('admin/customers/list.html', customers=customers)

@admin_bp.route('/customers/view/<int:customer_id>')
@login_required
@permission_required('manage_customers')
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('admin/customers/view.html', customer=customer)

@admin_bp.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
@permission_required('manage_customers')
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    # Log activity
    log = ActivityLog(
        admin_user_id=current_user.id,
        action=f"Deleted customer '{customer.name}' (ID: {customer.id})"
    )
    db.session.add(log)
    db.session.commit()
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('admin.list_customers'))

# Activity Logs
@admin_bp.route('/activity_logs')
@login_required
@permission_required('view_activity_logs')
def view_activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/activity_logs/list.html', logs=logs)

# Admin logout route
@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/users')
@login_required
@permission_required('view_users')  # Replace with the correct permission if needed
def list_users():
    users = AdminUser.query.all()  # Fetch all admin users
    return render_template('admin/users/list.html', users=users)

@admin_bp.route('/users/view/<int:user_id>')
@login_required
@permission_required('view_users')
def view_user(user_id):
    user = AdminUser.query.get_or_404(user_id)
    return render_template('admin/users/view.html', user=user)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_users')
def edit_user(user_id):
    user = AdminUser.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]  # Populate role choices

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)  # Update password only if provided
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.list_users'))

    return render_template('admin/users/edit.html', form=form, user=user)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('delete_users')
def delete_user(user_id):
    user = AdminUser.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted successfully.", "success")
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/roles', methods=['GET'])
@login_required
@permission_required('view_roles')
def list_roles():
    roles = Role.query.all()
    return render_template('admin/roles/list.html', roles=roles)
