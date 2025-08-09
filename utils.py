import os
from zipfile import ZipFile

import convertapi
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

def apply_watermark(input_path, watermark_img_path, scale, position, output_folder):
    doc = fitz.open(input_path)
    wm_img = Image.open(watermark_img_path).convert("RGBA")
    new_width = int(wm_img.width * scale)
    new_height = int(wm_img.height * scale)
    wm_img_resized = wm_img.resize((new_width, new_height), Image.LANCZOS)

    temp_wm_path = os.path.join(output_folder, "temp_watermark.png")
    wm_img_resized.save(temp_wm_path, "PNG")

    for page in doc:
        img_rect = fitz.Rect(position[0], position[1], position[0] + new_width, position[1] + new_height)
        page.insert_image(img_rect, filename=temp_wm_path, overlay=True)

    output_pdf = os.path.join(output_folder, "watermarked.pdf")
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()
    os.remove(temp_wm_path)
    return output_pdf

def compress_pdf(input_pdf_path, output_folder):
  convertapi.api_credentials = "Vlw2QGbmaQIBYJdjSiqrqyNQoJp3zbKa"
  os.makedirs(output_folder, exist_ok=True)
  convertapi.convert('compress', {
    'File': input_pdf_path,
    'Preset': 'web'
}, from_format = 'pdf').save_files(output_folder)

def split_pdf(input_pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(input_pdf_path)
    split_files = []
    for i in range(len(doc)):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        output_path = os.path.join(output_folder, f"{i + 1}.pdf")
        new_doc.save(output_path, garbage=4, deflate=True, clean=True)
        new_doc.close()
        split_files.append(output_path)
    doc.close()
    return split_files

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)