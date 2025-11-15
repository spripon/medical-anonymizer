# 🏥 Anonymiseur de Documents Médicaux

Application Streamlit complète pour anonymiser automatiquement les documents médicaux en supprimant les informations d’identification des patients.

## 🎯 Fonctionnalités

### Anonymisation automatique des :

- ✅ **Dates** (format JJ/MM/AAAA)
- ✅ **Numéros longs** (6+ chiffres)
- ✅ **Emails**
- ✅ **Numéros de téléphone**
- ✅ **Numéros de sécurité sociale**
- ✅ **Noms et prénoms**
- ✅ **Informations personnalisables** (établissement, médecin, etc.)

### Formats supportés :

- 📄 **PDF** (avec masquage visuel)
- 📝 **Word** (DOCX)
- 📋 **Fichiers texte** (TXT)
- 🖼️ **Images** (PNG, JPG, JPEG, GIF, BMP, TIFF)

### Fonctionnalités avancées :

- 🔍 **OCR (Reconnaissance optique de caractères)** pour détecter le texte dans les images
- 🎨 **Détection automatique des zones de texte** avec OpenCV
- 📊 **Rapport détaillé** des anonymisations effectuées
- 🖥️ **Interface intuitive** et facile à utiliser
- 👁️ **Aperçu avant/après** pour les images

## 🚀 Installation et Déploiement

### Option 1 : Déploiement sur Streamlit Cloud (Recommandé)

#### Étape 1 : Créer le repository GitHub

1. Créez un nouveau repository sur GitHub
1. Clonez le repository localement :

```bash
git clone https://github.com/votre-username/medical-anonymizer.git
cd medical-anonymizer
```

#### Étape 2 : Ajouter les fichiers

1. Créez les fichiers suivants dans le repository :
- `app.py` (le script principal)
- `requirements.txt` (les dépendances)
- `README.md` (ce fichier)
- `.gitignore` (fichiers à ignorer)
- `packages.txt` (dépendances système - voir ci-dessous)
1. Créez un fichier `packages.txt` pour Tesseract OCR :

```txt
tesseract-ocr
tesseract-ocr-fra
tesseract-ocr-eng
```

1. Commitez et pushez :

```bash
git add .
git commit -m "Initial commit - Medical Document Anonymizer with Image Support"
git push origin main
```

#### Étape 3 : Déployer sur Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
1. Connectez-vous avec votre compte GitHub
1. Cliquez sur “New app”
1. Sélectionnez :
- **Repository** : votre-username/medical-anonymizer
- **Branch** : main
- **Main file path** : app.py
1. Cliquez sur **“Deploy”**

⏱️ Le déploiement prend environ 5-10 minutes.

### Option 2 : Installation locale

Si vous souhaitez tester l’application localement :

#### Prérequis système

**Sur Ubuntu/Debian :**

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

**Sur macOS :**

```bash
brew install tesseract tesseract-lang
```

**Sur Windows :**

1. Téléchargez et installez Tesseract depuis : https://github.com/UB-Mannheim/tesseract/wiki
1. Ajoutez le chemin d’installation à votre PATH

#### Installation Python

```bash
# Cloner le repository
git clone https://github.com/votre-username/medical-anonymizer.git
cd medical-anonymizer

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur macOS/Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

L’application sera accessible à l’adresse : http://localhost:8501

## 🔧 Utilisation

### 1️⃣ Configuration

- Sélectionnez les **champs à anonymiser** dans la barre latérale
- Ajoutez des **labels personnalisés** si nécessaire
- Pour les images, activez/désactivez l’**OCR** selon vos besoins

### 2️⃣ Upload

- **Téléchargez** votre document médical
- Formats acceptés : PDF, DOCX, TXT, PNG, JPG, JPEG, GIF, BMP, TIFF

### 3️⃣ Anonymisation

- **Cliquez** sur “Anonymiser le document”
- Visualisez les **statistiques** et le **rapport détaillé**

### 4️⃣ Téléchargement

- **Téléchargez** le document anonymisé
- Pour les images, comparez l’**avant/après**

## 📸 Anonymisation des images

### Comment ça marche ?

L’application utilise deux méthodes complémentaires :

1. **OCR (Tesseract)** :
- Détecte le texte dans l’image
- Identifie les dates, numéros, emails, etc.
- Masque les zones de texte détectées
1. **Détection de contours (OpenCV)** :
- Détecte automatiquement les zones de texte
- Masque les en-têtes (30% supérieur de l’image)
- Particulièrement efficace pour les documents scannés

### Conseils pour de meilleurs résultats :

- ✅ Utilisez des images de **haute qualité** (300 DPI minimum)
- ✅ Assurez-vous que le texte est **lisible** et **contrasté**
- ✅ Évitez les images **floues** ou **pixellisées**
- ✅ Pour les documents scannés, utilisez le format **PNG** ou **TIFF**

## ⚠️ Avertissements et Sécurité

### ⚠️ IMPORTANT - Vérification manuelle requise

Cette application est un **outil d’aide** à l’anonymisation. Il est **IMPÉRATIF** de :

- ✅ **Vérifier manuellement** chaque document anonymisé
- ✅ S’assurer que **toutes les données sensibles** ont été correctement supprimées
- ✅ **Tester** l’application avec des documents non sensibles avant utilisation
- ✅ Respecter les **réglementations** en vigueur (RGPD, HIPAA, etc.)
- ❌ **Ne jamais se fier uniquement** à l’automatisation pour des documents critiques

### 🔒 Sécurité et Confidentialité

- ✅ **Aucun document n’est stocké** sur les serveurs
- ✅ Le traitement est effectué **en temps réel**
- ✅ Les fichiers sont **supprimés immédiatement** après téléchargement
- ✅ **Aucune donnée n’est conservée** ou transmise à des tiers
- ✅ Le code est **open source** et vérifiable

### Limitations connues

- L’OCR peut ne pas détecter du texte manuscrit
- Les images de très mauvaise qualité peuvent avoir des résultats incomplets
- Les documents complexes avec mise en page spéciale nécessitent une vérification accrue
- Le masquage est définitif et irréversible

## 📦 Structure du projet

```
medical-anonymizer/
│
├── app.py                 # Application Streamlit principale
├── requirements.txt       # Dépendances Python
├── packages.txt          # Dépendances système (Tesseract)
├── README.md             # Documentation
├── .gitignore            # Fichiers à ignorer par Git
│
└── (optionnel)
    ├── tests/            # Tests unitaires
    └── examples/         # Exemples de documents
```

## 🛠️ Technologies utilisées

- **Streamlit** : Interface utilisateur
- **PyMuPDF (fitz)** : Traitement des PDF
- **python-docx** : Traitement des fichiers Word
- **Pillow (PIL)** : Traitement des images
- **Tesseract OCR** : Reconnaissance optique de caractères
- **OpenCV** : Détection de contours et zones de texte
- **pandas** : Gestion des données tabulaires
- **NumPy** : Calculs numériques

## 🐛 Résolution des problèmes

### Erreur : “Tesseract not found”

**Solution** :

- Assurez-vous que Tesseract est installé sur votre système
- Sur Streamlit Cloud, vérifiez que `packages.txt` existe et contient les bonnes dépendances

### Erreur : “OCR non disponible”

**Solution** :

- L’application continuera de fonctionner avec la détection de contours OpenCV
- Désactivez l’option OCR dans la barre latérale si nécessaire

### Les images ne s’anonymisent pas correctement

**Solutions** :

- Vérifiez la qualité de l’image (résolution, contraste)
- Essayez avec l’OCR activé/désactivé
- Utilisez une image au format PNG pour de meilleurs résultats

## 📝 Changelog

### Version 2.0.0 (Actuelle)

- ✨ Ajout du support des images (PNG, JPG, JPEG, GIF, BMP, TIFF)
- ✨ Intégration de l’OCR (Tesseract)
- ✨ Détection automatique des zones de texte avec OpenCV
- ✨ Aperçu avant/après pour les images
- 🎨 Interface améliorée

### Version 1.0.0

- 📄 Support PDF, Word, TXT
- 🔍 Détection automatique des patterns
- 📊 Rapport détaillé des anonymisations

## 🤝 Contributions

Les contributions sont les bienvenues ! Pour contribuer :

1. **Forkez** le projet
1. Créez une **branche** pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
1. **Commitez** vos changements (`git commit -m 'Add AmazingFeature'`)
1. **Pushez** vers la branche (`git push origin feature/AmazingFeature`)
1. Ouvrez une **Pull Request**

### Idées de contributions

- 🔄 Amélioration de la détection OCR
- 🌍 Support multilingue
- 📊 Export des rapports en PDF/Excel
- 🎨 Personnalisation de l’interface
- 🧪 Ajout de tests unitaires

## 📄 Licence

Ce projet est fourni **“tel quel”** sans garantie d’aucune sorte.

**Utilisation :**

- ✅ Libre d’utilisation pour un usage personnel ou professionnel
- ✅ Modification et adaptation autorisées
- ⚠️ Aucune garantie de résultat
- ⚠️ Les utilisateurs sont responsables de la conformité réglementaire

## 📧 Support et Contact

- 🐛 **Bugs** : Ouvrez une issue sur GitHub
- 💡 **Suggestions** : Ouvrez une issue avec le tag “enhancement”
- 📖 **Documentation** : Consultez ce README
- 💬 **Questions** : Utilisez les Discussions GitHub

## 🙏 Remerciements

Merci à tous les contributeurs et aux équipes derrière :

- Streamlit
- Tesseract OCR
- OpenCV
- PyMuPDF

## ⭐ Si ce projet vous est utile

N’hésitez pas à :

- ⭐ **Mettre une étoile** au repository
- 🔀 **Forker** le projet
- 📢 **Partager** avec vos collègues
- 🐛 **Reporter** les bugs
- 💡 **Suggérer** des améliorations

-----

**Développé avec ❤️ pour la protection des données patients**

*Dernière mise à jour : Novembre 2025
