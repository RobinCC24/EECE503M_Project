from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.sql import text


app = Flask(__name__,template_folder='frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define Order Model
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, nullable=False)  
    status = db.Column(db.String(50), nullable=False, default='Pending')
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

# Define Return Model
class Return(db.Model):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('returns.order_id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    issued_refunds = db.Column(db.Boolean, default=False)
    offered_replacement = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)

def insert_example_orders():
    if Order.query.count() == 0:
        db.session.add(Order(order_id=1, product_id=1, status='Pending', total_price=150.0, order_date=datetime.utcnow()))
        db.session.add(Order(order_id=2, product_id=2, status='Completed', total_price=200.0, order_date=datetime.utcnow()))
        db.session.add(Order(order_id=3, product_id=3, status='Shipped', total_price=100.0, order_date=datetime.utcnow()))
        db.session.commit()
       
# Create tables
def create_tables():
    db.create_all()

# Sample Route: Create an Order
@app.route('/api/orders', methods=['POST'])
def create_order():
    """Add a new user to the database."""
   # Get JSON data from the request
    data = request.get_json()
    product_id = data.get('product_id')
    status=data.get('status', 'Pending')
    total_price=data.get('total_price', 0.0)
    order_date = data.get('order_date', datetime.utcnow().isoformat())  # Optional: manually set order_date
    
    # Validate input data
    if not product_id or not status or not total_price:
        return jsonify({"error": "Product ID, Status and Total Price are required fields"}), 400
    try:
        # Parameterized query to insert a new order (order_id is auto-generated)
        rawQueryString = """
        INSERT INTO 'orders' (product_id, status, total_price, order_date) 
        VALUES (:product_id, :status, :total_price, :order_date)
        """
        query = text(rawQueryString).bindparams(
            product_id=product_id,
            status=status,
            total_price=total_price,
            order_date=order_date  # Set the order date manually
        )
        db.session.execute(query)
        db.session.commit()  # Commit the transaction
        
        return jsonify({"message": "Order created successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    
# Sample Route: Get All Orders
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        rawQueryString = f"SELECT * FROM 'orders'"
        query = text(rawQueryString)
        result = db.session.execute(query)
        rows = result.fetchall()
        result_list = [{"order_id": row.order_id, "product_id": row.product_id, "status": row.status, "total_price": row.total_price, "order_date": row.order_date} for row in rows]
        return jsonify(result_list)
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

# Sample Route: Get Order by ID
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        # Use parameterized query to prevent SQL injection
        rawQueryString = "SELECT * FROM 'orders' WHERE order_id = :order_id"
        query = text(rawQueryString).bindparams(order_id=order_id)
        result = db.session.execute(query)
        row = result.fetchone()  # Fetch only one row since we are looking up by ID
        # Check if the order was found
        if row is None:
            return jsonify({"error": "Order not found"}), 404
        # Convert row to a dictionary
        order_data = {"order_id": row.order_id, "product_id": row.product_id, "status": row.status, "total_price": row.total_price, "order_date": row.order_date}

        # Return the user data as JSON
        return jsonify(order_data), 200

    except SQLAlchemyError as e:
        # Handle any database errors
        return jsonify({"error": "Database error", "details": str(e)}), 500

# Sample Route: Update Order Status
@app.route('/api/returns', methods=['POST'])
def create_return():
    data = request.json
    try:
        order = Order.query.get(data['order_id'])
        if not order:
            return jsonify({"error": "Order not found"}), 404
        product_id = data.get('product_id')
        return_entry = Return(
            order_id=data['order_id'],
            reason=data['reason'],
            issued_refunds=data.get('issued_refunds', False),
            offered_replacement=data.get('offered_replacement', False)
        )
        db.session.add(return_entry)
        if return_entry.issued_refunds:
            order.status = "Closed"   
        if return_entry.offered_replacement:
            new_product_id = data.get('new_product_id')
            if new_product_id:
                order.product_id = new_product_id
            else:
                return jsonify({"error": "New product ID required for replacement"}), 400
        db.session.commit()
        return jsonify({"message": "Return created successfully", "order_status":order.status }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

# Sample Route: Delete an Order
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        # Check if the order exists
        query = text("SELECT * FROM 'orders' WHERE order_id = :order_id").bindparams(order_id=order_id)
        result = db.session.execute(query)
        order = result.fetchone()
        if order is None:
            # If order doesn't exist, return a 404 response
            return jsonify({"error": "Order not found"}), 404
        # Delete the user if they exist
        delete_query = text("DELETE FROM 'orders' WHERE order_id = :order_id").bindparams(order_id=order_id)
        db.session.execute(delete_query)
        db.session.commit()  # Commit the transaction
        return jsonify({"message": "Order deleted successfully"}), 200
    except SQLAlchemyError as e:
        # Roll back in case of error
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

# Sample Route: Generate Invoice
@app.route('/api/orders/<int:order_id>/invoice', methods=['GET'])
def generate_invoice(order_id):
    try:
        # Use parameterized query to prevent SQL injection
        rawQueryString = "SELECT * FROM 'orders' WHERE order_id = :order_id"
        query = text(rawQueryString).bindparams(order_id=order_id)
        result = db.session.execute(query)
        row = result.fetchone()  # Fetch only one row since we are looking up by ID
        # Check if the user was found
        if row is None:
            return jsonify({"error": "Order not found"}), 404
        # Convert row to a dictionary
        invoice = f""" Invoice for Order ID #{row.order_id}, Product ID: {row.product_id}, Status: {row.status}, Total Price: ${row.total_price}, Order Date: {row.order_date}. Thank you for your purchase! """
        # Return the user data as JSON
        return jsonify(invoice), 200

    except SQLAlchemyError as e:
        # Handle any database errors
        return jsonify({"error": "Database error", "details": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables in the database
        insert_example_orders()
    app.run(debug=True, port=4000)