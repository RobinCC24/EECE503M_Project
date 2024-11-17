from app import create_app
from extensions import db
from models.ecommerce_models import Warehouse, Product, Inventory

app = create_app()

with app.app_context():
    # Clear existing data (optional)
    Inventory.query.delete()
    Warehouse.query.delete()
    db.session.commit()

    # Add sample warehouses
    warehouses = [
        Warehouse(location="Main Warehouse"),
        Warehouse(location="Downtown Store"),
        Warehouse(location="Uptown Store"),
    ]
    db.session.add_all(warehouses)
    db.session.commit()

    # Link products to warehouses in inventory
    products = Product.query.all()  # Ensure you have products in your DB
    if not products:
        print("No products found. Please add products first.")
        exit()

    for warehouse in warehouses:
        for product in products:
            inventory_record = Inventory(
                product_id=product.id,
                warehouse_id=warehouse.id,
                quantity=10  # Set a default quantity
            )
            db.session.add(inventory_record)
    db.session.commit()

    print("Warehouses and inventory records added successfully!")
