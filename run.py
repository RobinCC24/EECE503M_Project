from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ssl_context = ('app/security/certificate.crt', 'app/security/private.key')
    app.run(debug=True, ssl_context=ssl_context)
