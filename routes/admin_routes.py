from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from pymysql import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db, AdminUser, Role, Permission
from forms.admin_forms import LoginForm, AdminUserForm, RoleForm
from extensions import login_manager

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
    return render_template('login.html', form=form)

# Admin dashboard route
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# List all admin users
@admin_bp.route('/users')
@login_required
@permission_required('manage_users')
def list_users():
    users = AdminUser.query.all()
    return render_template('users/list.html', users=users)

# Create an admin user
@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def create_user():
    form = AdminUserForm()
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
    if form.validate_on_submit():
        existing_user = AdminUser.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash(f"Email '{form.email.data}' is already taken.", 'danger')
            return render_template('users/create.html', form=form)

        user = AdminUser(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role_id.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        try:
            db.session.commit()
            flash('Admin user created successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists. Please use a different email.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {e}", 'danger')
    return render_template('users/create.html', form=form)

# Edit an admin user
@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def edit_user(user_id):
    user = db.session.query(AdminUser).get_or_404(user_id)
    form = AdminUserForm(obj=user)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        try:
            if user.role and user.role.name == 'SuperAdmin':
                superadmin_count = AdminUser.query.filter(
                    AdminUser.role.has(name='SuperAdmin')
                ).count()

                if superadmin_count == 1 and form.role_id.data != user.role_id:
                    flash(
                        "There must be at least one SuperAdmin user. You cannot change this user's role.",
                        'danger',
                    )
                    return redirect(url_for('admin.edit_user', user_id=user.id))

            user.username = form.username.data
            user.email = form.email.data
            user.role_id = form.role_id.data

            if form.password.data:
                user.password_hash = generate_password_hash(form.password.data)

            db.session.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", 'danger')
    return render_template('users/edit.html', form=form)

# Delete an admin user
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('manage_users')
def delete_user(user_id):
    try:
        user = db.session.query(AdminUser).get(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.list_users'))

        if user.username == 'superadmin':
            flash('Cannot delete SuperAdmin user.', 'danger')
            return redirect(url_for('admin.list_users'))

        db.session.delete(user)
        db.session.commit()
        flash('Admin user deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {e}", 'danger')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/admin/roles')
def list_roles():
    roles = Role.query.all()
    for role in roles:
        print(f"Role: {role.name}, Permissions: {[p.name for p in role.permissions]}")
    return render_template('roles/list.html', roles=roles)

@admin_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
def create_role():
    form = RoleForm()
    form.permissions.choices = [(p.id, p.name) for p in Permission.query.all()]

    if form.validate_on_submit():
        role_name = form.name.data
        permission_ids = form.permissions.data

        role = Role(name=role_name)
        permissions = db.session.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions.extend(permissions)

        try:
            db.session.add(role)
            db.session.commit()
            flash('Role created successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.list_roles'))

    return render_template('roles/create.html', form=form)

@admin_bp.route('/admin/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    try:
        # Fetch the role and all permissions
        role = db.session.query(Role).get(role_id)
        if not role:
            flash('Role not found.', 'danger')
            return redirect(url_for('admin.list_roles'))

        permissions = Permission.query.all()

        if request.method == 'POST':
            role.name = request.form['name']

            # Clear existing permissions and update with the selected ones
            selected_permissions = request.form.getlist('permissions')

            # Use db.session.merge to ensure the permissions are part of the current session
            role.permissions = []
            for permission_id in selected_permissions:
                permission = db.session.query(Permission).get(permission_id)
                if permission:
                    role.permissions.append(db.session.merge(permission))

            db.session.commit()
            flash('Role updated successfully!', 'success')
            return redirect(url_for('admin.list_roles'))

        return render_template('roles/edit.html', role=role, permissions=permissions)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating role: {str(e)}', 'danger')
        return redirect(url_for('admin.list_roles'))
@admin_bp.route('/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    try:
        role = db.session.query(Role).get(role_id)
        if role:
            db.session.delete(role)
            db.session.commit()
            flash('Role deleted successfully.', 'success')
        else:
            flash('Role not found.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('admin.list_roles'))

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))
