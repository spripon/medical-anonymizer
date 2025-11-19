import streamlit as st
import spacy
import re
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw
import io
import numpy as np
import os
from docx import Document
from fpdf import FPDF

st.set_page_config(page_title="Anonymiseur Médical", page_icon="🏥", layout="wide")

# --- CHARGEMENT DU MODÈLE ---
@st.cache_resource
def load_nlp_model():
    # On essaie de charger le modèle installé via requirements.txt
    try:
        return spacy.load("fr_core_news_md")
    except OSError:
        st.warning("Modèle 'md' introuvable, tentative de chargement du fallback...")
        # Fallback de secours si le nommage interne diffère
        import fr_core_news_md
        return fr_core_news_md.load()

try:
    nlp = load_nlp_model()
except Exception as e:
    st.error(f"Erreur de chargement du modèle : {e}")
    st.stop()

# --- FONCTIONS D'ANALYSE ---
def get_sensitive_entities(text):
    sensitive_words = set()
    doc = nlp(text)
    
    # 1. Via Spacy (Noms, Lieux, Org)
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC", "ORG"]:
            sensitive_words.add(ent.text.lower())
            # Ajouter aussi les parties individuelles des noms longs
            for token in ent:
                if len(token.text) > 2:
                    sensitive_words.add(token.text.lower())

    # 2. Via Regex (Dates, Tel, Secu, Email)
    # Dates
    dates = re.findall(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', text)
    sensitive_words.update([d.lower() for d in dates])
    
    # Tel (formats variés)
    phones = re.findall(r'\b(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}\b', text)
    for p in phones:
        sensitive_words.add(p)
        # Ajouter les fragments (ex: les groupes de 2 chiffres)
        parts = re.split(r'[\s.-]', p)
        for part in parts:
            if len(part) > 1:
                sensitive_words.add(part)

    # NIR / Sécu
    ssns = re.findall(r'\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}(?:\s?\d{2})?\b', text)
    sensitive_words.update([s.replace(" ", "") for s in ssns])

    # Emails
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    sensitive_words.update([e.lower() for e in emails])

    return sensitive_words

def should_redact(word, sensitive_set):
    clean_word = word.lower().strip('.,:;()[]"\'')
    if clean_word in sensitive_set:
        return True
    # Regex de sécurité sur le mot seul (dates isolées)
    if re.match(r'^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$', clean_word):
        return True
    return False

# --- TRAITEMENT IMAGE ---
def anonymize_image_page(image):
    # 1. OCR global pour le contexte
    full_text = pytesseract.image_to_string(image, lang='fra')
    sensitive_entities = get_sensitive_entities(full_text)
    
    # 2. OCR positionnel
    data = pytesseract.image_to_data(image, lang='fra', output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(image)
    n_boxes = len(data['text'])
    
    for i in range(n_boxes):
        word = data['text'][i]
        conf = int(data['conf'][i])
        if conf > 0 and word.strip():
            if should_redact(word, sensitive_entities):
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                # Dessin du rectangle noir
                draw.rectangle([x, y, x + w, y + h], fill="black", outline="black")
    return image

# --- TRAITEMENT WORD ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Document Anonymisé', 0, 1, 'C')

def process_docx(file_bytes):
    source_stream = io.BytesIO(file_bytes)
    doc = Document(source_stream)
    full_text = [para.text for para in doc.paragraphs]
    text_content = "\n".join(full_text)
    
    sensitive_entities = get_sensitive_entities(text_content)
    anonymized_text = text_content
    
    # Remplacement du texte
    sorted_entities = sorted(list(sensitive_entities), key=len, reverse=True)
    for entity in sorted_entities:
        pattern = re.compile(re.escape(entity), re.IGNORECASE)
        anonymized_text = pattern.sub("█" * len(entity), anonymized_text)

    # Génération PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    safe_text = anonymized_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("🛡️ Anonymiseur Médical")
uploaded_file = st.file_uploader("Fichier (PDF, DOCX, IMG)", type=["pdf", "docx", "png", "jpg", "jpeg"])

if uploaded_file:
    if st.button("Anonymiser"):
        with st.spinner("Traitement..."):
            output = None
            ftype = uploaded_file.type
            
            if ftype in ["image/png", "image/jpeg", "image/jpg"]:
                img = Image.open(uploaded_file).convert("RGB")
                res = anonymize_image_page(img)
                res.save("temp.pdf", "PDF")
                with open("temp.pdf", "rb") as f: output = f.read()
                st.image(res, "Résultat")
                
            elif ftype == "application/pdf":
                imgs = convert_from_bytes(uploaded_file.read())
                res_imgs = [anonymize_image_page(img) for img in imgs]
                if res_imgs:
                    res_imgs[0].save("temp.pdf", save_all=True, append_images=res_imgs[1:])
                    with open("temp.pdf", "rb") as f: output = f.read()
            
            elif "word" in ftype:
                output = process_docx(uploaded_file.read())
                
            if output:
                st.success("Terminé !")
                st.download_button("Télécharger PDF", output, "anonymise.pdf", "application/pdf")
