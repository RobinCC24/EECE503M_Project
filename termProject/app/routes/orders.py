from flask import Blueprint, request, jsonify
from app.models import db, Order, Customer  # Import the db and models

orders_bp = Blueprint('orders_bp', __name__)


@orders_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(
        customer_id=data['customer_id'],
        product_id=data['product_id'],
        status='pending',
        quantity=data['quantity'],
        total_price=data['total_price']
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'message': 'Order created successfully', 'order_id': new_order.id})

@orders_bp.route('/orders/<int:order_id>/update_status', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'message': 'Order status updated successfully'})

@orders_bp.route('/orders/<int:order_id>/return', methods=['POST'])
def process_return(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'returned'
    db.session.commit()
    return jsonify({'message': 'Order returned and processed for refund'})
