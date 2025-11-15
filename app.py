import os
import re
import streamlit as st
import tempfile
from io import BytesIO
from datetime import datetime

# Bibliothèques pour le traitement des fichiers
import PyPDF2
import pdfplumber
from docx import Document
from docx.shared import Inches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit

# Pour le traitement NLP (optionnel, pour une meilleure détection des noms)
try:
    import spacy
    NLP_AVAILABLE = True
    # Charger le modèle français (à installer séparément avec: python -m spacy download fr_core_news_sm)
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        st.warning("Le modèle NLP français n'est pas installé. Utilisation des expressions régulières uniquement.")
        NLP_AVAILABLE = False
except ImportError:
    NLP_AVAILABLE = False
    st.warning("La bibliothèque spaCy n'est pas installée. Utilisation des expressions régulières uniquement.")

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Anonymisation de Documents Médicaux",
    page_icon="🏥",
    layout="wide"
)

# Fonctions pour le traitement des fichiers
def extract_text_from_pdf(file):
    """Extrait le texte d'un fichier PDF."""
    text = ""
    try:
        # Utilisation de pdfplumber pour une meilleure extraction
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte du PDF: {str(e)}")
        # Fallback avec PyPDF2
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e2:
            st.error(f"Erreur avec la méthode alternative: {str(e2)}")
            return None
    return text

def extract_text_from_docx(file):
    """Extrait le texte d'un fichier Word (.docx)."""
    try:
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte du document Word: {str(e)}")
        return None

def create_pdf_from_text(text, filename):
    """Crée un fichier PDF à partir du texte traité."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Définir les marges
    margin = 72
    y_position = height - margin
    line_height = 14
    
    # Diviser le texte en lignes pour l'affichage
    lines = text.split('\n')
    
    for line in lines:
        # Vérifier si nous avons besoin d'une nouvelle page
        if y_position < margin:
            p.showPage()
            y_position = height - margin
        
        # Diviser les lignes longues pour qu'elles tiennent dans la page
        wrapped_lines = simpleSplit(line, "Helvetica", 10, width - 2 * margin)
        
        for wrapped_line in wrapped_lines:
            if y_position < margin:
                p.showPage()
                y_position = height - margin
            
            p.drawString(margin, y_position, wrapped_line)
            y_position -= line_height
    
    p.save()
    buffer.seek(0)
    return buffer

def create_docx_from_text(text, filename):
    """Crée un fichier Word (.docx) à partir du texte traité."""
    doc = Document()
    
    # Ajouter le texte au document
    for line in text.split('\n'):
        doc.add_paragraph(line)
    
    # Sauvegarder dans un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Fonctions d'anonymisation
def anonymize_with_regex(text):
    """Anonymise le texte en utilisant des expressions régulières."""
    if not text:
        return text
    
    # Remplacer les dates au format JJ/MM/AAAA
    text = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', '[DATE]', text)
    
    # Remplacer les dates au format JJ-MM-AAAA
    text = re.sub(r'\b\d{2}-\d{2}-\d{4}\b', '[DATE]', text)
    
    # Remplacer les dates au format AAAA-MM-JJ
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '[DATE]', text)
    
    # Remplacer les numéros de téléphone (français)
    text = re.sub(r'\b0[1-9]([-. ]?[0-9]{2}){4}\b', '[TÉLÉPHONE]', text)
    
    # Remplacer les numéros longs (potentiellement des identifiants)
    text = re.sub(r'\b\d{8,}\b', '[ID]', text)
    
    # Remplacer les adresses e-mail
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Remplacer les codes postaux (français)
    text = re.sub(r'\b[0-9]{5}\b', '[CODE POSTAL]', text)
    
    # Remplacer les âges
    text = re.sub(r'\b(\d{1,2})\s*(ans|an)\b', r'[ÂGE: \1 ans]', text)
    
    # Remplacer les numéros de sécurité sociale (français)
    text = re.sub(r'\b[12]\s*([0-9]{2})\s*([0-9]{2})\s*([0-9]{3})\s*([0-9]{3})\s*([0-9]{2})\s*([0-9]{2})\b', '[SÉCURITÉ SOCIALE]', text)
    
    # Remplacer les motifs courants dans les documents médicaux
    text = re.sub(r'(?i)(nom\s*:\s*)([A-Z][a-z]+\s*[A-Z][a-z]+)', r'\1[NOM]', text)
    text = re.sub(r'(?i)(prénom\s*:\s*)([A-Z][a-z]+)', r'\1[PRÉNOM]', text)
    text = re.sub(r'(?i)(n°\s*patient\s*:\s*)(\w+)', r'\1[ID PATIENT]', text)
    text = re.sub(r'(?i)(patient\s*:\s*)([A-Z][a-z]+\s*[A-Z][a-z]+)', r'\1[PATIENT]', text)
    text = re.sub(r'(?i)(date\s*d[\'\u2019]étude\s*:\s*)(\d{2}/\d{2}/\d{4})', r'\1[DATE]', text)
    text = re.sub(r'(?i)(effectué\s*par\s*:\s*)([A-Z][a-z]+\s*[A-Z][a-z]+)', r'\1[MÉDECIN]', text)
    text = re.sub(r'(?i)(établissement\s*:\s*)([A-Z][a-z]+\s*[A-Z][a-z]+)', r'\1[ÉTABLISSEMENT]', text)
    
    return text

def anonymize_with_nlp(text):
    """Anonymise le texte en utilisant le traitement NLP pour détecter les noms propres."""
    if not text or not NLP_AVAILABLE:
        return text
    
    try:
        doc = nlp(text)
        anonymized_text = text
        
        # Détecter et remplacer les entités nommées de type PERSON
        for ent in doc.ents:
            if ent.label_ == "PER" or ent.label_ == "PERSON":
                anonymized_text = anonymized_text.replace(ent.text, "[NOM]")
        
        return anonymized_text
    except Exception as e:
        st.error(f"Erreur lors de l'anonymisation NLP: {str(e)}")
        return text

def anonymize_text(text, use_nlp=True):
    """Fonction principale d'anonymisation qui combine regex et NLP."""
    if not text:
        return text
    
    # D'abord, utiliser les expressions régulières
    anonymized = anonymize_with_regex(text)
    
    # Ensuite, utiliser NLP si disponible et demandé
    if use_nlp and NLP_AVAILABLE:
        anonymized = anonymize_with_nlp(anonymized)
    
    return anonymized

# Interface utilisateur Streamlit
def main():
    st.title("🏥 Anonymisation de Documents Médicaux")
    st.markdown("""
    Cette application permet d'anonymiser des documents médicaux en supprimant les informations d'identification du patient.
    
    Les informations suivantes seront masquées :
    - Noms de patients
    - Numéros de patients
    - Âges
    - Noms d'établissements
    - Dates (format JJ/MM/AAAA)
    - Numéros de téléphone
    - Adresses e-mail
    - Codes postaux
    - Numéros de sécurité sociale
    - Numéros longs (identifiants potentiels)
    """)
    
    # Options de traitement
    st.sidebar.header("Options de traitement")
    use_nlp = st.sidebar.checkbox("Utiliser le NLP pour détecter les noms propres", value=True, 
                                  help="Améliore la détection des noms propres mais nécessite plus de temps de traitement.")
    
    # Upload du fichier
    uploaded_file = st.file_uploader(
        "Téléchargez un document médical (PDF ou Word)",
        type=["pdf", "docx"]
    )
    
    if uploaded_file is not None:
        file_details = {
            "Nom du fichier": uploaded_file.name,
            "Type de fichier": uploaded_file.type,
            "Taille": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        st.write("### Détails du fichier")
        st.json(file_details)
        
        # Extraction du texte
        st.write("### Extraction du texte")
        with st.spinner("Extraction du texte en cours..."):
            if uploaded_file.type == "application/pdf":
                original_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                original_text = extract_text_from_docx(uploaded_file)
            else:
                st.error("Type de fichier non pris en charge.")
                return
        
        if original_text:
            st.success("Texte extrait avec succès!")
            
            # Afficher un aperçu du texte original
            with st.expander("Aperçu du texte original"):
                st.text_area("Texte original", original_text, height=300)
            
            # Anonymisation
            st.write("### Anonymisation")
            with st.spinner("Anonymisation en cours..."):
                anonymized_text = anonymize_text(original_text, use_nlp)
            
            st.success("Anonymisation terminée!")
            
            # Afficher un aperçu du texte anonymisé
            with st.expander("Aperçu du texte anonymisé"):
                st.text_area("Texte anonymisé", anonymized_text, height=300)
            
            # Création du fichier de sortie
            st.write("### Création du fichier anonymisé")
            
            # Déterminer le type de fichier de sortie
            output_format = st.radio(
                "Format du fichier de sortie",
                ["PDF", "Word (.docx)"],
                index=0 if uploaded_file.type == "application/pdf" else 1
            )
            
            # Bouton pour télécharger le fichier anonymisé
            if st.button("Générer et télécharger le fichier anonymisé"):
                with st.spinner("Génération du fichier en cours..."):
                    # Créer le nom de fichier de sortie
                    base_filename = os.path.splitext(uploaded_file.name)[0]
                    output_filename = f"{base_filename}_anonymized"
                    
                    if output_format == "PDF":
                        buffer = create_pdf_from_text(anonymized_text, output_filename)
                        st.download_button(
                            label="Télécharger le PDF anonymisé",
                            data=buffer,
                            file_name=f"{output_filename}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        buffer = create_docx_from_text(anonymized_text, output_filename)
                        st.download_button(
                            label="Télécharger le document Word anonymisé",
                            data=buffer,
                            file_name=f"{output_filename}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                
                st.success("Fichier anonymisé prêt à être téléchargé!")

if __name__ == "__main__":
    main()
