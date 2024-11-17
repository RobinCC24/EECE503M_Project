from flask import Blueprint, request, jsonify  # For routing, handling requests, and JSON responses
from models.ecommerce_models import db, Customer, Order
  # Import db and models for database operations
customers_bp = Blueprint('customers_bp', __name__)

@customers_bp.route('/customers/<int:customer_id>', methods=['GET'])
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer.id).all()
    return jsonify({
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'membership_tier': customer.membership_tier,
        'orders': [{'id': order.id, 'status': order.status, 'total_price': order.total_price} for order in orders]
    })


@customers_bp.route('/customers/<int:customer_id>/update_tier', methods=['PUT'])
def update_membership_tier(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json()
    customer.membership_tier = data.get('membership_tier', customer.membership_tier)
    db.session.commit()
    return jsonify({'message': 'Customer membership tier updated successfully'})


@customers_bp.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    new_customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        address=data['address'],
        membership_tier=data.get('membership_tier', 'Standard')
    )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'Customer created successfully', 'customer_id': new_customer.id})