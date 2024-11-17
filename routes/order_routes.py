from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from datetime import datetime
from models.ecommerce_models import Order, Customer  # Assuming Order and Customer are in ecommerce_models

# Define the blueprint
order_bp = Blueprint('orders', __name__, url_prefix='/api')

# Create an Order
@order_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()

    try:
        # Create a new order instance
        new_order = Order(
            customer_id=data.get('customer_id'),
            product_id=data.get('product_id'),
            status=data.get('status', 'Pending'),
            quantity=data.get('quantity', 1),
            total_price=data.get('total_price', 0.0),
            order_date=datetime.utcnow(),
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'message': 'Order created successfully', 'order_id': new_order.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500


# Get All Orders
@order_bp.route('/orders', methods=['GET'])
def get_orders():
    try:
        # Fetch all orders
        orders = Order.query.all()
        result_list = [
            {
                "order_id": order.id,
                "customer_id": order.customer_id,
                "product_id": order.product_id,
                "status": order.status,
                "quantity": order.quantity,
                "total_price": order.total_price,
                "order_date": order.order_date,
            }
            for order in orders
        ]
        return jsonify(result_list)
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


# Delete an Order
@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        # Check if the order exists and delete it
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        return jsonify({"message": "Order deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500


# Update Order Status
@order_bp.route('/orders/<int:order_id>/update_status', methods=['PUT'])
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        order.status = data.get('status', order.status)
        db.session.commit()
        return jsonify({'message': 'Order status updated successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500


# Process Return
@order_bp.route('/orders/<int:order_id>/return', methods=['POST'])
def process_return(order_id):
    try:
        # Mark the order as returned
        order = Order.query.get_or_404(order_id)
        order.status = 'returned'
        db.session.commit()
        return jsonify({'message': 'Order returned and processed for refund'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
