#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
anonymizer.py
Anonymisation ciblée de documents médicaux (PDF + images) par OCR.

Masqué UNIQUEMENT :
  1) Noms/prénoms du patient : mots capitalisés après :
     - "Monsieur", "Mr", "M.", "Madame", "Mme", "Mlle", "Mademoiselle".
  2) Noms/prénoms des médecins : mots capitalisés après :
     - "Docteur", "Dr", "dr", "Dr.".
  3) Noms d'établissements de santé :
     - "Hôpital / Hopital / Hôpitaux de <Ville>"
     - "Centre hospitalier de <Ville>"
     - "CHU <Ville>"
  4) Adresses :
     - "<numéro> rue/route/boulevard/bd/blv/avenue/av./impasse/allée/chemin/place ..."
       → masqué du numéro jusqu'à la fin de la ligne.
  5) Dates :
     - JJ/MM/AAAA, JJ.MM.AAAA, JJ/MM/AA, JJ.MM.AA.
  6) Numéros :
     - numéros de téléphone (séquences avec ≥ 7 chiffres),
     - tout nombre contenant ≥ 7 chiffres.
  7) Codes-barres / QR-codes :
     - détectés par analyse d'image (contours rectangulaires denses en “encre”).

Entrée : PDF ou image (PNG, JPG/JPEG, GIF, TIFF).
Sortie : PDF anonymisé (mêmes pages, mais avec rectangles blancs serrés sur les zones ciblées).
"""

import os
import re
from typing import List, Tuple

from PIL import Image, ImageDraw
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path

import numpy as np
import cv2


# ---------- RÉGEX & LISTES UTILITAIRES ----------

DATE_REGEX = re.compile(
    r"\b([0-3]?\d)[./]([0-1]?\d)[./](\d{2}|\d{4})\b"
)

PHONE_REGEX = re.compile(r"\+?\d[\d\s.\-]{6,}\d")
LONG_NUMBER_REGEX = re.compile(r"\b\d{7,}\b")

TITLE_PATIENT = {
    "monsieur", "mr", "m.", "madame", "mme", "mlle", "mademoiselle"
}

TITLE_DOCTOR = {
    "docteur", "dr", "dr.", "drs"
}

ROAD_TYPES = {
    "rue", "route", "rte", "boulevard", "bd", "blv", "av", "av.",
    "avenue", "impasse", "allee", "allée", "chemin", "place"
}


def normalize_word(w: str) -> str:
    return w.strip().strip(".,;:()[]{}<>/\\\"'«»!?")


def is_capitalized(word: str) -> bool:
    """
    Nom propre de type "Candelier", "Serrano", "Lannemezan" ou "CANDELIER".
    On considère qu'un mot est "nom propre" s'il commence par une majuscule
    (ou est tout en majuscules), longueur >= 2.
    """
    w = normalize_word(word)
    if len(w) < 2:
        return False
    if w[0].isupper():
        return True
    return False


def count_digits(text: str) -> int:
    return sum(ch.isdigit() for ch in text)


# ---------- DÉTECTION CODES-BARRES / QR-CODES ----------

def detect_barcode_like_regions(img: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Détection heuristique de régions de type codes-barres / QR-codes :
    - contours rectangulaires,
    - aire minimale,
    - forte densité de pixels “encre”,
    - aspect ratio compatible (0.5–6).

    Retourne une liste de bounding boxes (x1, y1, x2, y2).
    """
    gray = np.array(img.convert("L"))

    # Texte + codes en blanc, fond en noir
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[Tuple[int, int, int, int]] = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < 1500:
            continue

        aspect = w / float(h)
        if aspect < 0.5 or aspect > 6.0:
            continue

        roi = thr[y:y + h, x:x + w]
        white_ratio = np.mean(roi == 255)

        # On garde les régions très denses
        if white_ratio < 0.35:
            continue

        boxes.append((x, y, x + w, y + h))

    return boxes


# ---------- DÉTECTION TEXTE À MASQUER ----------

def detect_pii_boxes_from_ocr(ocr: dict) -> List[Tuple[int, int, int, int]]:
    """
    Analyse le résultat de pytesseract.image_to_data et renvoie
    une liste de rectangles à masquer (x1, y1, x2, y2) autour des mots ciblés.
    """
    boxes: List[Tuple[int, int, int, int]] = []

    n = len(ocr["text"])
    line_dict = {}

    for i in range(n):
        text = ocr["text"][i]
        conf = float(ocr["conf"][i])

        if not text or text.strip() == "" or conf < 0:
            continue

        page = ocr["page_num"][i]
        block = ocr["block_num"][i]
        par = ocr["par_num"][i]
        line = ocr["line_num"][i]
        key = (page, block, par, line)

        left = ocr["left"][i]
        top = ocr["top"][i]
        width = ocr["width"][i]
        height = ocr["height"][i]

        if key not in line_dict:
            line_dict[key] = {
                "words": [],
                "bbox": [left, top, left + width, top + height],
            }
        else:
            x1, y1, x2, y2 = line_dict[key]["bbox"]
            nx1 = min(x1, left)
            ny1 = min(y1, top)
            nx2 = max(x2, left + width)
            ny2 = max(y2, top + height)
            line_dict[key]["bbox"] = [nx1, ny1, nx2, ny2]

        line_dict[key]["words"].append(
            {
                "text": text,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "conf": conf,
            }
        )

    for key, line in line_dict.items():
        words = line["words"]
        line_text = " ".join(w["text"] for w in words)

        # 1) DATES & NOMBRES LONGS (par mot)
        for w in words:
            t = w["text"].strip()
            if DATE_REGEX.search(t):
                boxes.append(_bbox_word(w))
                continue
            if LONG_NUMBER_REGEX.search(t):
                boxes.append(_bbox_word(w))
                continue

        # 2) Numéros de téléphone / numéros à ≥ 7 chiffres
        for w in words:
            t = w["text"]
            if PHONE_REGEX.search(t) or count_digits(t) >= 7:
                boxes.append(_bbox_word(w))

        # 3) ADRESSES : "<num> rue/route/bd/..." → du numéro à la fin de la ligne
        for i, w in enumerate(words):
            txt = normalize_word(w["text"])
            if txt.isdigit():
                if i + 1 < len(words):
                    next_txt = normalize_word(words[i + 1]["text"]).lower()
                    if next_txt in ROAD_TYPES:
                        addr_bbox = _bbox_range(words, i, len(words) - 1)
                        boxes.append(addr_bbox)
                        break

        # 4) NOMS PATIENTS : après "Monsieur / Madame / Mr / Mme / Mlle ..."
        for i, w in enumerate(words):
            low = normalize_word(w["text"]).lower()
            if low in TITLE_PATIENT:
                j = i + 1
                cap_count = 0
                while j < len(words) and cap_count < 3:
                    if is_capitalized(words[j]["text"]):
                        boxes.append(_bbox_word(words[j]))
                        cap_count += 1
                        j += 1
                    else:
                        break

        # 5) NOMS MÉDECINS : après "Docteur / Dr / dr"
        for i, w in enumerate(words):
            low = normalize_word(w["text"]).lower()
            if low in TITLE_DOCTOR:
                j = i + 1
                cap_count = 0
                while j < len(words) and cap_count < 3:
                    if is_capitalized(words[j]["text"]):
                        boxes.append(_bbox_word(words[j]))
                        cap_count += 1
                        j += 1
                    else:
                        break

        # 6) ÉTABLISSEMENTS DE SANTÉ
        for i, w in enumerate(words):
            txt_norm = normalize_word(w["text"])
            low = txt_norm.lower()

            # Hôpital / Hopital / Hôpitaux de X...
            if low in {"hopital", "hôpital", "hopitaux"}:
                start = i
                end = i
                if i + 1 < len(words):
                    low_next = normalize_word(words[i + 1]["text"]).lower()
                    if low_next in {"de", "d'"}:
                        end = i + 1
                j = end + 1
                cap_count = 0
                while j < len(words) and cap_count < 3:
                    if is_capitalized(words[j]["text"]):
                        end = j
                        cap_count += 1
                        j += 1
                    else:
                        break
                boxes.append(_bbox_range(words, start, end))

            # Centre hospitalier de X...
            if low == "centre" and i + 1 < len(words):
                low_next = normalize_word(words[i + 1]["text"]).lower()
                if low_next.startswith("hospitalier"):
                    start = i
                    end = i + 1
                    j = i + 2
                    if j < len(words):
                        low_j = normalize_word(words[j]["text"]).lower()
                        if low_j in {"de", "d'"}:
                            end = j
                            j += 1
                    cap_count = 0
                    while j < len(words) and cap_count < 3:
                        if is_capitalized(words[j]["text"]):
                            end = j
                            cap_count += 1
                            j += 1
                        else:
                            break
                    boxes.append(_bbox_range(words, start, end))

            # CHU X...
            if low == "chu":
                start = i
                end = i
                j = i + 1
                cap_count = 0
                while j < len(words) and cap_count < 3:
                    if is_capitalized(words[j]["text"]):
                        end = j
                        cap_count += 1
                        j += 1
                    else:
                        break
                boxes.append(_bbox_range(words, start, end))

    return boxes


def _bbox_word(w: dict) -> Tuple[int, int, int, int]:
    x1 = w["left"]
    y1 = w["top"]
    x2 = x1 + w["width"]
    y2 = y1 + w["height"]
    return (x1, y1, x2, y2)


def _bbox_range(words: List[dict], i_start: int, i_end: int) -> Tuple[int, int, int, int]:
    xs1, ys1, xs2, ys2 = [], [], [], []
    for i in range(i_start, i_end + 1):
        w = words[i]
        x1 = w["left"]
        y1 = w["top"]
        x2 = x1 + w["width"]
        y2 = y1 + w["height"]
        xs1.append(x1)
        ys1.append(y1)
        xs2.append(x2)
        ys2.append(y2)
    return (min(xs1), min(ys1), max(xs2), max(ys2))


# ---------- TRAITEMENT D'UNE IMAGE ----------

def anonymize_image(img: Image.Image) -> Image.Image:
    """
    OCR + détection des PII + masquage (rectangles blancs serrés).
    Ajout de la détection des codes-barres / QR-codes.
    """
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    ocr_data = pytesseract.image_to_data(
        img, output_type=Output.DICT, lang="fra+eng"
    )

    boxes_text = detect_pii_boxes_from_ocr(ocr_data)
    boxes_barcode = detect_barcode_like_regions(img)

    boxes = boxes_text + boxes_barcode

    draw = ImageDraw.Draw(img)
    margin = 2  # petite marge pour couvrir le mot sans manger la ligne voisine

    for (x1, y1, x2, y2) in boxes:
        draw.rectangle(
            [(x1 - margin, y1 - margin), (x2 + margin, y2 + margin)],
            fill="white",
        )

    return img


# ---------- PIPELINE PDF & IMAGES ----------

def process_pdf(input_path: str) -> List[Image.Image]:
    pages = convert_from_path(input_path, dpi=300)
    processed = []
    for page in pages:
        anon_page = anonymize_image(page)
        processed.append(anon_page)
    return processed


def process_image_file(input_path: str) -> List[Image.Image]:
    img = Image.open(input_path)
    anon = anonymize_image(img)
    return [anon]


def save_images_as_pdf(images: List[Image.Image], output_path: str) -> None:
    if not images:
        raise ValueError("Aucune image à sauvegarder.")

    images_rgb = []
    for im in images:
        if im.mode != "RGB":
            images_rgb.append(im.convert("RGB"))
        else:
            images_rgb.append(im)

    first, *rest = images_rgb
    first.save(
        output_path,
        "PDF",
        save_all=True,
        append_images=rest,
        resolution=300.0,
    )


def anonymize_document_to_pdf(input_path: str, output_path: str) -> None:
    """
    Fonction de haut niveau utilisée par Streamlit :
    lit input_path (PDF ou image) et écrit un PDF anonymisé dans output_path.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        images = process_pdf(input_path)
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff"]:
        images = process_image_file(input_path)
    else:
        raise ValueError("Format non supporté (utilise PDF ou image).")

    save_images_as_pdf(images, output_path)
