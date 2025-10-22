import os
from zipfile import ZipFile

import convertapi
import fitz  # PyMuPDF
import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
aPDF_key = os.getenv("aPDF_key")
WOW = os.getenv("WOW")

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

def compress_pdf2(input_pdf_path, output_folder):
  convertapi.api_credentials = WOW
  os.makedirs(output_folder, exist_ok=True)
  convertapi.convert('compress', {
    'File': input_pdf_path,
    'Preset': 'web'
}, from_format = 'pdf').save_files(output_folder)

def compress_pdf(input_pdf_path, output_pdf_path, quality="low", token=aPDF_key):
    # url = "http://apdf.localhost/api/pdf/compress"
    url = "http://127.0.0.1:8501/api/pdf/compress"


    headers = {
        "Authorization": f"Bearer {aPDF_key}"
    }

    with open(input_pdf_path, "rb") as f:
        response = requests.post(
            url,
            headers=headers,
            files={"file": f},
            data={"quality": quality}
        )

    if response.status_code == 200 and response.headers.get("Content-Type") == "application/pdf":
        with open(output_pdf_path, "wb") as out:
            out.write(response.content)
        print(f"Compressed PDF saved to {output_pdf_path}")
        return True
    else:
        print("Compression failed:", response.status_code, response.text)
        return False

def compress_pdf2(input_pdf_path, output_pdf_path, token):
    with open(input_pdf_path, "rb") as f:
        upload_resp = requests.post("https://file.io", files={"file": f})
    if upload_resp.status_code != 200:
        print("Failed to upload file for compression:", upload_resp.text)
        return False
    file_url = upload_resp.json().get("link")
    if not file_url:
        print("Upload did not return a valid URL")
        return False
    url = "https://apdf.io/api/pdf/file/compress"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"file": file_url}

    resp = requests.post(url, headers=headers, data=data)
    if resp.status_code != 200:
        print("Compression failed:", resp.status_code, resp.text)
        return False

    compressed_url = resp.json().get("file")
    if not compressed_url:
        print("API did not return a compressed file URL")
        return False

    compressed_resp = requests.get(compressed_url)
    if compressed_resp.status_code != 200:
        print("Failed to download compressed PDF")
        return False

    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    with open(output_pdf_path, "wb") as f:
        f.write(compressed_resp.content)

    print(f"Compressed PDF saved to {output_pdf_path}")
    return True


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