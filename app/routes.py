import requests
from flask import render_template, flash, redirect, url_for, request
from . import db
from .models import Track, Review, User
from .forms import SearchForm, ReviewForm, TrackForm
from flask_login import current_user, login_required, login_user, logout_user
from flask import current_app as app
from .forms import LoginForm, RegistrationForm # Assure-toi d'avoir créé ce formulaire dans forms.py
from functools import wraps
from flask import abort
import os

if os.getenv("USE_PROXY") == "True":
    proxies = {"http": "http://172.16.0.51:8080", "https": "http://172.16.0.51:8080"}
else:
    proxies = None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Accès interdit
        return f(*args, **kwargs)
    return decorated_function

def apply_db_priority(api_data_list):
    """
    Prend une liste de tracks venant de l'API Deezer 
    et remplace les infos par celles de la BDD si elles existent.
    """
    # 1. On prépare la liste des IDs à chercher en BDD
    api_ids = []
    for track in api_data_list:
        track_id_str = str(track["id"])
        api_ids.append(track_id_str)

    # 2. Une seule requête pour trouver toutes les tracks existantes
    tracks_in_db = Track.query.filter(
        Track.deezer_id.in_(api_ids)
    ).all()

    # 3. On crée un dictionnaire (map) pour retrouver facilement les tracks
    tracks_map = {}
    for t in tracks_in_db:
        tracks_map[t.deezer_id] = t

    # 4. On applique les changements
    for track_api in api_data_list:
        current_id = str(track_api["id"])
        
        if current_id in tracks_map:
            track_db = tracks_map[current_id]
            
            # On écrase les données de l'API par celles de l'Admin
            track_api["title"] = track_db.title
            track_api["artist"]["name"] = track_db.artist
            track_api["album"]["cover_medium"] = track_db.cover_medium
            
    return api_data_list

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    all_reviews = Review.query.order_by(Review.date_posted.desc()).all()
    all_tracks = Track.query.all()
    return render_template('admin/dashboard.html', reviews=all_reviews, tracks=all_tracks)

# --- CRUD TRACKS POUR ADMIN ---

@app.route('/admin/track/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_track():
    form = TrackForm()
    
    if form.validate_on_submit():
        # On crée un nouvel objet Track vide
        new_track = Track()
        # On "déverse" les données du formulaire dans l'objet new_track
        form.populate_obj(new_track)
        
        db.session.add(new_track)
        db.session.commit()
        
        flash("Track ajoutée avec succès !", "success")
        return redirect(url_for('admin_dashboard'))
    
    # On passe form au template, et track=None pour que le bouton affiche "Ajouter"
    return render_template('admin/edit_track.html', form=form, track=None)

@app.route('/admin/track/delete/<int:track_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    # Attention : Supprimer une track supprimera ses reviews en cascade (si configuré)
    db.session.delete(track)
    db.session.commit()
    flash("Track et ses avis supprimés.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/track/edit/<int:track_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_track(track_id):
    track = Track.query.get_or_404(track_id)
    
    # On pré-remplit le formulaire avec les données actuelles de la base
    form = TrackForm(obj=track)

    if form.validate_on_submit():
        # On met à jour l'objet 'track' existant avec les nouvelles saisies
        form.populate_obj(track)
        
        db.session.commit()
        flash(f"Le titre '{track.title}' a été mis à jour.", "success")
        return redirect(url_for('admin_dashboard'))

    # On passe l'objet track pour que le template puisse afficher l'image actuelle
    return render_template('admin/edit_track.html', form=form, track=track)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # On vérifie si l'utilisateur existe déjà
        user_exists = User.query.filter_by(email=form.email.data).first()
        if user_exists:
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('register'))

        # Création du nouvel utilisateur
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Hachage automatique ici

        db.session.add(user)
        db.session.commit()

        flash('Compte créé avec succès ! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('search'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('search'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = []

    if form.validate_on_submit():
        query = form.search.data
        response = requests.get(f"https://api.deezer.com/search?q={query}", proxies=proxies, timeout=5)

        if response.status_code == 200:
            api_data = response.json().get('data', [])

            # APPEL DE LA FONCTION UNIQUE ICI
            results = apply_db_priority(api_data)

    return render_template('search.html', form=form, results=results)


@app.route('/review/<int:deezer_id>', methods=['GET', 'POST'])
@login_required
def add_review(deezer_id):
    form = ReviewForm()

    # 1. On récupère d'abord les infos de l'API pour l'affichage (sans enregistrer en BDD encore)
    response = requests.get(f"https://api.deezer.com/track/{deezer_id}", proxies=proxies, timeout=5)

    if response.status_code != 200:
        flash("Musique introuvable sur Deezer.", "danger")
        return redirect(url_for('search'))

    data = response.json()

    # --- UTILISATION DE LA FONCTION ---
    # On met 'data' dans une liste [] pour la fonction, 
    # puis on récupère le premier élément [0]
    data = apply_db_priority([data])[0]
    # ----------------------------------

    print(data["title"])

    # 2. Traitement lors de la validation du formulaire (SUBMIT)
    if form.validate_on_submit():
        # A. Vérifier si la track existe déjà en BDD pour éviter les doublons
        track = Track.query.filter_by(deezer_id=str(deezer_id)).first()
        
        # B. Si elle n'existe pas, on la crée à ce moment précis
        if not track:
            track = Track(
                deezer_id=str(deezer_id),
                title=data['title'],
                artist=data['artist']['name'],
                cover_medium=data['album']['cover_medium'],
                cover_big = data['album']['cover_big'],
                preview = data['preview']

            )
            db.session.add(track)
            db.session.flush()  # Récupère l'ID de la track sans terminer la transaction

        # C. Création de l'avis lié à cette track
        new_review = Review(
            content=form.content.data,
            rating=form.rating.data,
            user_id=current_user.id,
            track_id=track.id  # On utilise l'ID de la track (nouvelle ou existante)
        )

        db.session.add(new_review)
        db.session.commit()  # On valide tout d'un coup en BDD

        flash("Votre avis a été ajouté !", "success")
        return redirect(url_for('search'))

    # Pour le GET : on passe 'data' au template pour afficher les infos de la musique
    return render_template('add_review.html', form=form, track=data)

@app.route('/review/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    # SÉCURITÉ : Vérifier que l'auteur est bien l'utilisateur connecté
    if review.author != current_user and not current_user.is_admin:
        flash("Vous n'avez pas l'autorisation de modifier cet avis.", "danger")
        return redirect(url_for('my_reviews'))

    form = ReviewForm(obj=review)

    if form.validate_on_submit():
        form.populate_obj(review)

        db.session.commit()
        flash("L'avis a été mis à jour par l'administration." if current_user.is_admin else "L'avis a été avis a été mis à jour !", "success")
        return redirect(request.referrer or url_for('index'))

    return render_template('edit_review.html', form=form, track=review.track)

@app.route('/review/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    # SÉCURITÉ : Vérifier que l'auteur est bien l'utilisateur connecté
    if review.author != current_user and not current_user.is_admin:
        flash("Action non autorisée.", "danger")
        return redirect(url_for('my_reviews'))

    db.session.delete(review)
    db.session.commit()
    flash("L'avis a été supprimé par l'administration." if current_user.is_admin else "L'avis a été supprimé.", "info")
    return redirect(request.referrer or url_for('index'))


# Voir details d'une track

@app.route('/track/<int:deezer_id>')
def track_details(deezer_id):
    # 1. Récupérer les infos de la track depuis l'API
    response = requests.get(f"https://api.deezer.com/track/{deezer_id}", proxies=proxies, timeout=5)

    if response.status_code != 200:
        flash("Musique introuvable sur Deezer.", "danger")
        return redirect(url_for('search'))

    data = response.json()

    # APPEL DE LA FONCTION UNIQUE ICI
    data = apply_db_priority([data])[0]

    # 2. Récupérer les avis liés à cette track depuis la BDD
    track_in_db = Track.query.filter_by(deezer_id=str(deezer_id)).first()
    reviews = track_in_db.reviews if track_in_db else []

    return render_template('track_details.html', track=data, reviews=reviews)