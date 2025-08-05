import os
import shutil
from zipfile import ZipFile
import fitz 
import streamlit as st


def compress_and_split_pdf(input_path, output_folder):
    doc = fitz.open(input_path)
    os.makedirs(output_folder, exist_ok=True)
    for i, page in enumerate(doc):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.set_metadata({})
        out_path = os.path.join(output_folder, f"{i+1}.pdf")
        new_doc.save(out_path, garbage=4, deflate=True, clean=True)
        new_doc.close()
    doc.close()

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)

st.title("Compressed & Split PDF")
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    working_dir = "split_output"
    split_folder = os.path.join(working_dir, "pages")
    zip_output = os.path.join(working_dir, "numbered_pages.zip")

    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(split_folder, exist_ok=True)

    input_path = os.path.join(working_dir, "input.pdf")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    compress_and_split_pdf(input_path, split_folder)
    zip_folder(split_folder, zip_output)

    with open(zip_output, "rb") as f:
        st.download_button("Download Split ZIP", f, file_name="modifiedPDFs.zip")

    shutil.rmtree(working_dir)