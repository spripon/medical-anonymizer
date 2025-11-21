#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

import streamlit as st
from PIL import Image

from anonymizer import anonymize_document_to_pdf


st.set_page_config(
    page_title="Anonymiseur de documents médicaux",
    page_icon="🩺",
    layout="centered",
)

st.title("🩺 Anonymiseur de documents médicaux")
st.write(
    """
Téléverse un document médical **(PDF ou photo : PNG, JPG, JPEG, GIF, TIFF)**.

L'application :
- lit le texte par OCR,
- masque automatiquement :
  - les noms/prénoms après *Monsieur/Madame/Docteur/Dr*,
  - les noms d'établissements de santé (*Hôpital de..., CHU..., Centre hospitalier de...*),
  - les adresses (ex. **“644 route de Toulouse ...”**),
  - **toutes les dates** au format JJ/MM/AAAA ou JJ.MM.AAAA,
  - les numéros de téléphone et **tous les numéros ≥ 7 chiffres**,
  - les codes-barres / QR-codes détectés sur l'image.
Le PDF résultant est **identique visuellement** mais avec des rectangles blancs serrés sur les zones anonymisées.
"""
)

uploaded_file = st.file_uploader(
    "Choisis un document à anonymiser",
    type=["pdf", "png", "jpg", "jpeg", "gif", "tif", "tiff"],
)

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()

    st.write(f"**Fichier chargé :** `{uploaded_file.name}`")

    # Aperçu si c'est une image
    if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff"]:
        try:
            img = Image.open(uploaded_file)
            st.image(img, caption="Aperçu du document original", use_column_width=True)
        except Exception:
            st.info("Prévisualisation image impossible, mais le fichier sera traité.")

    st.markdown("---")
    if st.button("Anonymiser le document"):
        with st.spinner("Anonymisation en cours..."):
            try:
                # On écrit le fichier uploadé dans un fichier temporaire
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_in:
                    tmp_in.write(uploaded_file.getbuffer())
                    input_path = tmp_in.name

                # Fichier de sortie temporaire (toujours PDF)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                    output_path = tmp_out.name

                # Traitement
                anonymize_document_to_pdf(input_path, output_path)

                # On lit le PDF anonymisé pour le proposer en téléchargement
                with open(output_path, "rb") as f:
                    pdf_bytes = f.read()

                st.success("Anonymisation terminée.")

                st.download_button(
                    label="📥 Télécharger le PDF anonymisé",
                    data=pdf_bytes,
                    file_name=f"anonymise_{os.path.splitext(uploaded_file.name)[0]}.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"Erreur lors de l'anonymisation : {e}")

            finally:
                # Nettoyage des fichiers temporaires
                try:
                    if 'input_path' in locals() and os.path.exists(input_path):
                        os.remove(input_path)
                except Exception:
                    pass
                try:
                    if 'output_path' in locals() and os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
else:
    st.info("Téléverse un fichier pour commencer.")
