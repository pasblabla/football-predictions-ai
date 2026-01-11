from wsgi import app
from src.models.football import db

with app.app_context():
    db.create_all()
    print("Base de données créée avec succès")
