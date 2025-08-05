import os
import shutil
from zipfile import ZipFile

import fitz  # PyMuPDF
import streamlit as st
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from streamlit_drawable_canvas import st_canvas

# ----------------- Watermark + Compress + Split ------------------

def apply_watermark_and_split(pdf_path, watermark_img, position, output_folder):
    doc = fitz.open(pdf_path)
    os.makedirs(output_folder, exist_ok=True)

    wm_img = Image.open(watermark_img)
    wm_width, wm_height = wm_img.size
    wm_img_path = "watermark_temp.png"
    wm_img.save(wm_img_path)

    for i, page in enumerate(doc):
        page_width, page_height = page.rect.width, page.rect.height

        # Adjust size and position
        img_rect = fitz.Rect(position[0], position[1],
                             position[0] + wm_width, position[1] + wm_height)
        page.insert_image(img_rect, filename=wm_img_path, overlay=True)

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.set_metadata({})

        out_path = os.path.join(output_folder, f"{i+1}.pdf")
        new_doc.save(out_path, garbage=4, deflate=True, clean=True)
        new_doc.close()

    doc.close()
    os.remove(wm_img_path)

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)

# ---------------------- Streamlit UI -----------------------------

st.set_page_config(page_title="PDF Watermark & Split", layout="wide")
st.title("📄 PDF Watermark ➜ Compress ➜ Split ➜ Download")

pdf_file = st.file_uploader("Upload PDF", type="pdf")
watermark_file = st.file_uploader("Upload Watermark Image (PNG/JPG)", type=["png", "jpg", "jpeg"])

if pdf_file and watermark_file:
    # Temp working dir
    working_dir = "split_output"
    split_folder = os.path.join(working_dir, "pages")
    zip_output = os.path.join(working_dir, "numbered_pages.zip")
    input_path = os.path.join(working_dir, "input.pdf")

    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(split_folder, exist_ok=True)

    # Save PDF
    with open(input_path, "wb") as f:
        f.write(pdf_file.read())

    # Extract first page as preview image
    doc = fitz.open(input_path)
    page_pix = doc[0].get_pixmap(dpi=100)
    preview_path = os.path.join(working_dir, "preview.png")
    page_pix.save(preview_path)
    doc.close()

    st.subheader("Drag to position watermark (on first page):")

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        background_image=Image.open(preview_path),
        update_streamlit=True,
        height=600,
        width=450,
        drawing_mode="transform",
        key="canvas",
        initial_drawing=[{"type": "image", "src": watermark_file, "width": 100, "height": 100}],
    )

    if st.button("Generate"):
        if canvas_result.json_data:
            # Get position from first object
            obj = canvas_result.json_data["objects"][0]
            left = obj.get("left", 0)
            top = obj.get("top", 0)

            # Use width/height from resized image
            width = obj.get("scaleX", 1) * obj.get("width", 100)
            height = obj.get("scaleY", 1) * obj.get("height", 100)

            position = (left, top)

            # Apply watermark, compress and split
            apply_watermark_and_split(input_path, watermark_file, position, split_folder)
            zip_folder(split_folder, zip_output)

            with open(zip_output, "rb") as f:
                st.success("✅ Done!")
                st.download_button("Download ZIP", f, file_name="numbered_split_pages.zip")
        else:
            st.warning("⚠️ Please drag/place the watermark before generating.")
