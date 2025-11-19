Anonymiseur de Documents Médicaux (RGPD)
Une application Python sécurisée construite avec Streamlit pour anonymiser automatiquement des documents médicaux (PDF, Word, Images). L'application détecte les informations personnelles (Noms, Dates, Téléphones, etc.) et applique un masquage visuel (bandeaux noirs) ou textuel.
Fonctionnalités
Entrées supportées : PDF, DOCX, JPG, PNG.
Sortie : PDF nettoyé.
Détection :
Reconnaissance d'entités nommées (NER) via Spacy (fr_core_news_lg) pour les noms, lieux et organisations.
Expressions régulières (Regex) pour les dates, numéros de sécurité sociale, téléphones.
Technique : Utilise Tesseract OCR pour "lire" les documents scannés et dessiner des rectangles noirs aux coordonnées exactes des données sensibles.
Installation Locale
Cloner le repo :
git clone [https://github.com/votre-username/medical-anonymizer.git](https://github.com/votre-username/medical-anonymizer.git)
cd medical-anonymizer


Créer un environnement virtuel :
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate


Installer les dépendances Python :
pip install -r requirements.txt


Important : Installer Tesseract OCR et Poppler sur votre machine.
Mac : brew install tesseract tesseract-lang poppler
Windows : Télécharger les installateurs pour Tesseract et Poppler et ajouter au PATH.
Linux : sudo apt-get install tesseract-ocr tesseract-ocr-fra poppler-utils
Lancer l'application :
streamlit run app.py


Déploiement sur Streamlit Cloud
Poussez ce code sur GitHub.
Créez un compte sur share.streamlit.io.
Connectez votre repo.
Streamlit détectera automatiquement packages.txt et installera Tesseract et Poppler, ainsi que les dépendances Python.
Avertissement
Cet outil est une aide à l'anonymisation. Une vérification humaine reste indispensable avant la diffusion de documents sensibles.
