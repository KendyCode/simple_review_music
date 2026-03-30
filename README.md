# 🎵 Music Log — Guide d'installation

> Application Flask de critique musicale connectée à l'API Deezer, avec gestion des utilisateurs et espace d'administration.

---

## 📋 Prérequis

- Python 3.x
- MariaDB installé et démarré
- pip
- Git

---

## ⚙️ 1. Créer l'environnement virtuel

```bash
python3 -m venv venv
```

---

## 🔌 2. Activer l'environnement virtuel

**Windows (PowerShell)** — si tu vois `PS` devant le chemin dans le terminal :

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS :**

```bash
source venv/bin/activate
```

> ✅ L'activation est réussie quand tu vois `(venv)` au début de ta ligne de commande.

---

## 🏫 3. (Lycée uniquement) Configurer le proxy

> ⚠️ **À faire AVANT `pip install` si tu es au lycée**, sinon pip ne pourra pas télécharger les paquets.

```bash
export http_proxy="http://172.16.0.51:8080"
export https_proxy="http://172.16.0.51:8080"
```

---

## 📦 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 🗄️ 5. Créer la base de données MariaDB

Connecte-toi à MariaDB :

```bash
mysql -u root -p
```

Puis crée ta base de données :

```sql
CREATE DATABASE nom_de_ta_base;
EXIT;
```

> Remplace `nom_de_ta_base` par le nom de ton choix (ex: `musiclog_db`).

---

## 🔐 6. Créer le fichier `.env`

Crée un fichier `.env` **à la racine du projet** (au même niveau que `run.py`) :

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_DEBUG=1

# Database Configuration (MySQL/MariaDB)
DB_USER=ton_utilisateur
DB_PASSWORD=ton_mot_de_passe
DB_HOST=localhost
DB_NAME=nom_de_ta_base

# Proxy (mettre True si tu es au lycée, False sinon)
USE_PROXY=False
```

> ⚠️ Ne commit **jamais** le fichier `.env` sur Git. Vérifie qu'il est bien dans ton `.gitignore`.

---

## 🔄 7. Appliquer les migrations

Si un dossier `migrations/` est déjà présent dans le projet :

```bash
flask db upgrade
```

---

## ▶️ 8. Lancer l'application

```bash
flask run
```

L'application sera accessible sur : [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 👑 9. Passer un utilisateur en administrateur

Après avoir créé un compte via l'interface web, ouvre un shell Python à la racine du projet :

```bash
python3
```

Puis exécute :

```python
from run import app
from app import db
from app.models import User

with app.app_context():
    # Remplace 'boss' par le pseudo du compte créé sur le site
    mon_user = User.query.filter_by(username='boss').first()
    mon_user.is_admin = True
    db.session.commit()
    print("Succès ! L'utilisateur est maintenant admin.")
```

> Remplace `'boss'` par le `username` du compte créé au préalable sur le site.  
> Une fois admin, l'utilisateur aura accès au tableau de bord `/admin/dashboard`.

---

## 🛑 .gitignore recommandé

```
venv/
.env
__pycache__/
*.pyc
instance/
```

---

## ❓ Problèmes fréquents

| Problème | Solution |
|---|---|
| `pip` ne télécharge rien au lycée | Configure le proxy (étape 3) |
| `flask db upgrade` échoue | Vérifie les identifiants dans `.env` et que MariaDB tourne |
| `Activate.ps1` refusé sous Windows | Exécute `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` dans PowerShell |
| Module introuvable | Vérifie que `(venv)` est bien actif dans ton terminal |

---

## 📖 À propos du projet

**Music Log** est une application web permettant à des utilisateurs de rechercher des morceaux de musique et de leur laisser des avis et des notes. Elle repose sur l'**API Deezer** pour les données musicales et sur une base de données locale pour stocker les avis, les utilisateurs et les personnalisations.

### Fonctionnalités principales

- 🔍 **Recherche de musique** via l'API Deezer en temps réel
- ⭐ **Système d'avis** : chaque utilisateur connecté peut noter et commenter un morceau
- 👤 **Gestion de compte** : inscription, connexion, déconnexion
- 🛡️ **Espace d'administration** : gestion des tracks et des avis via un tableau de bord dédié

### 🔗 Interconnexion Deezer / Base de données

Le projet repose sur une logique de **surcouche intelligente** entre l'API externe et la base de données locale.

**Priorité aux données locales (Override)**

Lors d'une recherche, le système interroge l'API Deezer normalement. Mais avant d'afficher les résultats, il vérifie si le `deezer_id` existe déjà dans la base de données locale. Si c'est le cas, les informations stockées en local (titre, artiste, pochette) **écrasent celles de l'API**. Cela permet à l'équipe de modération de corriger des métadonnées incorrectes ou de personnaliser l'affichage sans toucher à l'API.

**L'ajout administrateur (Pré-remplissage)**

Quand un administrateur utilise la fonction *Ajouter une Track*, il ne crée pas un morceau de zéro. Il doit obligatoirement renseigner un `deezer_id` réel et existant sur Deezer. En pratique, cette fonctionnalité sert à **pré-enregistrer** ou **modifier en avance** la façon dont un morceau Deezer apparaîtra sur Music Log — le système de notation et l'affichage détaillé continuant de s'appuyer sur les appels API liés à cet ID.

```
Recherche utilisateur
        │
        ▼
  API Deezer ──► deezer_id présent en BDD ?
                        │               │
                       OUI             NON
                        │               │
                        ▼               ▼
               Données locales    Données Deezer
               prioritaires           brutes
```