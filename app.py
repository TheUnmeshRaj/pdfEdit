import streamlit as st
import fitz
import os
from PIL import Image
import shutil
from utils import compress_pdf, apply_watermark, zip_folder, split_pdf

st.set_page_config(
    page_title="PDF Compressor & Splitter with Watermark",
    page_icon="🙏🏽",
    initial_sidebar_state="collapsed",
    layout="centered",
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
body {
    font-family: 'Inter', sans-serif;
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
""", unsafe_allow_html=True)

st.title("PDF Compressor & Splitter with Watermark")

# ---------- Step 1: Upload PDF ----------
st.markdown('<div class="step-header">📤 Step 1: Upload PDF File</div>', unsafe_allow_html=True)
uploaded_pdf = st.file_uploader("PDF File", type="pdf")

# ---------- Step 2: Watermark Upload ----------
st.markdown('<div class="step-header">🏷️ Step 2: Watermark Options (Optional)</div>', unsafe_allow_html=True)
uploaded_wm = st.file_uploader("Watermark", type=["png", "jpg", "jpeg"])

DEFAULT_WATERMARK_PATH = "watermark.png"
if uploaded_wm:
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

    # ---------- Extract first page preview ----------
    doc = fitz.open(input_pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.1, 1.1))
    pix.save(preview_img_path)
    page_rect_width, page_rect_height = page.rect.width, page.rect.height
    doc.close()
    preview_width, preview_height = Image.open(preview_img_path).size

    # ---------- Step 3: Watermark Placement ----------
    st.markdown('<div class="step-header">👁️ Step 3: Preview</div>', unsafe_allow_html=True)
    st.subheader("Exam Type")
    class_choice = st.radio(
        "Select class/board for automatic watermark placement defaults:",
        options=["Class 10", "Class 12"],
        horizontal=True,
    )
    default_scale, default_x, default_y = (26, 380, 520) if class_choice == "Class 10" else (30, 380, 700)

    l, c = st.columns([1.3, 2.2])
    with l:
        st.subheader("Watermark Placement")
        scale = st.slider("Size (%)", min_value=0, max_value=100, value=default_scale)
        scale_val = scale / 100.0
        x_pos = st.number_input("X (pixels)", 0, preview_width, value=default_x)
        y_pos = st.number_input("Y (pixels)", 0, preview_height, value=default_y)
        apply_btn = st.button("✅ Apply Watermark, Compress & Split")

    with c:
        with Image.open(preview_img_path) as preview_pil, Image.open(watermark_used).convert("RGBA") as wm_img:
            wm_resized = wm_img.resize(
                (int(wm_img.width * scale_val), int(wm_img.height * scale_val)), Image.LANCZOS
            )
            preview = preview_pil.convert("RGBA")
            preview.paste(wm_resized, (int(x_pos), int(y_pos)), wm_resized)
            st.image(preview, caption="Preview (first page)", use_column_width=True)

    if apply_btn:
        with st.spinner("Processing..."):
            pdf_x = int(x_pos * (page_rect_width / preview_width))
            pdf_y = int(y_pos * (page_rect_height / preview_height))

            watermarked_pdf_path = apply_watermark(
                input_pdf_path, watermark_used, scale=scale_val,
                position=(pdf_x, pdf_y), output_folder=working_dir
            )

            compress_pdf(watermarked_pdf_path, working_dir)
            compressed_pdf_path = os.path.join(working_dir, "watermarked.pdf")
            split_pdf(compressed_pdf_path, split_folder)
            zip_folder(split_folder, zip_output)

        st.success("✅ All done! Download your ZIP:")
        with open(zip_output, "rb") as f:
            st.download_button("⬇️ Download ZIP", f, file_name="PDFs.zip", use_container_width=True)

        shutil.rmtree(working_dir)
        if uploaded_wm and os.path.exists(wm_img_path):
            os.remove(wm_img_path)

else:
    st.info("Please upload a PDF to start.")

st.markdown("""
<footer style='text-align: center; color: #555; font-size: 0.93rem; margin-top: 2rem;'>
    Developed by Unmesh • Powered by PyMuPDF & Streamlit
</footer>
""", unsafe_allow_html=True)
