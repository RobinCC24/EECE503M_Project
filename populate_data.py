from app import create_app
from extensions import db
from models.ecommerce_models import Category, Subcategory

app = create_app()

with app.app_context():
    # Clear existing data
    Subcategory.query.delete()
    Category.query.delete()
    db.session.commit()

    # Define categories and subcategories
    data = {
        "String Instruments": ["Guitars", "Violins", "Cellos"],
        "Wind Instruments": ["Flutes", "Saxophones", "Clarinets"],
        "Percussion Instruments": ["Drums", "Tambourines", "Xylophones"],
        "Keyboards": ["Pianos", "Synthesizers", "Electric Keyboards"]
    }

    # Add to the database
    for category_name, subcategories in data.items():
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()
        for subcategory_name in subcategories:
            subcategory = Subcategory(name=subcategory_name, category_id=category.id)
            db.session.add(subcategory)
    db.session.commit()

    print("Categories and subcategories added successfully!")
