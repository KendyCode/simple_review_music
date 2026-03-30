from run import app
from app import db
from app.models import User

with app.app_context():
    # Chercher l'utilisateur par son pseudo
    mon_user = User.query.filter_by(username='boss').first()

    # Passer le statut admin à True
    mon_user.is_admin = True

    # Sauvegarder dans la base de données
    db.session.commit()
    print("Succès ! L'utilisateur est maintenant admin.")
