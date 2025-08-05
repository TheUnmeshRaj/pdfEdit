import os
import shutil
from zipfile import ZipFile

import fitz  # PyMuPDF
import streamlit as st
from PIL import Image


# ====== Utility Functions ======
def apply_watermark_to_pdf(input_path, watermark_img_path, scale, position, output_folder):
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
    watermarked_pdf_path = os.path.join(output_folder, "watermarked.pdf")
    doc.save(watermarked_pdf_path, garbage=4, deflate=True, clean=True)
    doc.close()
    os.remove(temp_wm_path)
    return watermarked_pdf_path

def compress_and_split_pdf(input_path, output_folder):
    doc = fitz.open(input_path)
    os.makedirs(output_folder, exist_ok=True)
    for i, page in enumerate(doc):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        out_path = os.path.join(output_folder, f"{i + 1}.pdf")
        new_doc.save(out_path, garbage=4, deflate=True, clean=True)
        new_doc.close()
    doc.close()

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)

# ====== Streamlit UI & Logic ======
st.set_page_config(
    page_title="PDF Compressor & Splitter with Watermark",
    page_icon="📄",
    initial_sidebar_state="collapsed",
    layout="centered",
)

# ----------- Style for Cloud & Local -----------
st.markdown(
    """
    <style>
    body {
        font-family: 'Inter', Arial, sans-serif;
        background-color: #f7f9fc;
        color: #222;
    }
    h1 {
        font-weight: 700;
        color: #619eff;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.18rem;
        color: #444;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(90deg, #0b3d91, #074080);
        color: white;
        padding: 0.7rem 1rem;
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.08rem;
    }
    .stDownloadButton > button {
        background-color: #0b3d91;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1.4rem;
        border-radius: 8px;
        border: none;
        transition: background 0.2s;
        margin-top: 0.8em;
    }
    .stDownloadButton > button:hover {
        background-color: #074080;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True
)

st.title("PDF Compressor & Splitter with Watermark")

# ----------- Step 1: Upload PDF -----------
st.markdown('<div class="step-header">📤 Step 1: Upload PDF File</div>', unsafe_allow_html=True)
uploaded_pdf = st.file_uploader("PDF File", type="pdf")

# ----------- Step 2: Watermark -----------
st.markdown('<div class="step-header">🏷️ Step 2: Watermark Options (Optional)</div>', unsafe_allow_html=True)
uploaded_wm = st.file_uploader("Watermark", type=["png", "jpg", "jpeg"])

DEFAULT_WATERMARK_PATH = "watermark.png"
if uploaded_wm is not None:
    wm_img_path = "temp_uploaded_wm.png"
    with open(wm_img_path, "wb") as f:
        f.write(uploaded_wm.read())
    watermark_used = wm_img_path
else:
    watermark_used = DEFAULT_WATERMARK_PATH

if uploaded_pdf:
    working_dir = "temp_processing"
    split_folder = os.path.join(working_dir, "split_pages")
    zip_output = os.path.join(working_dir, "output.zip")
    preview_img_path = os.path.join(working_dir, "preview.png")
    os.makedirs(working_dir, exist_ok=True)

    input_pdf_path = os.path.join(working_dir, "input.pdf")
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_pdf.read())

    # ---- Preview extraction ----
    doc = fitz.open(input_pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.1, 1.1))
    pix.save(preview_img_path)
    page_rect_width = page.rect.width
    page_rect_height = page.rect.height
    doc.close()
    with Image.open(preview_img_path) as preview_pil:
        preview_width, preview_height = preview_pil.size

    # ----------- Step 3: Placement/Preview -----------
    st.markdown('<div class="step-header">👁️ Step 3: Preview</div>', unsafe_allow_html=True)
    st.subheader("Exam Type")
    class_choice = st.radio(
        "Select class/board for automatic watermark placement defaults:",
        options=["Class 10", "Class 12"],
        horizontal=True,
    )
    if class_choice == "Class 10":
        default_scale = 26
        default_x = 380
        default_y = 520
    else:
        default_scale = 30
        default_x = 380
        default_y = 700

    l, c = st.columns([1.3, 2.2])
    with l:
        st.subheader("Watermark Placement")
        scale = st.slider("Size (%)", min_value=0, max_value=100, step=1, value=default_scale)
        scale_val = scale / 100.0
        x_pos = st.number_input("X (pixels)", min_value=0, max_value=preview_width, value=default_x)
        y_pos = st.number_input("Y (pixels)", min_value=0, max_value=preview_height, value=default_y)
        apply_btn = st.button("✅ Apply Watermark, Compress & Split")

    with c:
        with Image.open(preview_img_path) as preview_pil, Image.open(watermark_used).convert("RGBA") as wm_img:
            w, h = wm_img.size
            wm_resized = wm_img.resize((int(w * scale_val), int(h * scale_val)), Image.LANCZOS)
            preview = preview_pil.copy().convert("RGBA")
            preview.paste(wm_resized, (int(x_pos), int(y_pos)), wm_resized)
            st.image(preview, caption="Preview (first page with watermark)", use_column_width=True)

    if apply_btn:
        with st.spinner("Processing..."):
            pdf_scale_x = page_rect_width / preview_width
            pdf_scale_y = page_rect_height / preview_height
            pdf_x = int(x_pos * pdf_scale_x)
            pdf_y = int(y_pos * pdf_scale_y)
            # Watermark, compress/split, package
            watermarked_pdf_path = apply_watermark_to_pdf(
                input_pdf_path, watermark_used, scale=scale_val, position=(pdf_x, pdf_y), output_folder=working_dir
            )
            compress_and_split_pdf(watermarked_pdf_path, split_folder)
            zip_folder(split_folder, zip_output)
        st.success("✅ All done! Download your ZIP:")
        with open(zip_output, "rb") as f:
            st.download_button("⬇️ Download ZIP", f, file_name="PDFs.zip", use_column_width=True)
        shutil.rmtree(working_dir)
        if uploaded_wm is not None and os.path.exists(wm_img_path):
            os.remove(wm_img_path)
else:
    st.info("Please upload a PDF to start.")

st.markdown("""
    <footer style='text-align: center; color: #555; font-size: 0.93rem; margin-top: 2rem;'>
        Developed by Unmesh • Powered by PyMuPDF & Streamlit
    </footer>
    """, unsafe_allow_html=True,
)
