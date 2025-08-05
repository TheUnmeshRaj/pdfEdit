import os
import shutil
from zipfile import ZipFile
import fitz  # PyMuPDF
import streamlit as st

# --- Functions ---

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


st.set_page_config(
    page_title="PDF Compressor & Splitter",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Fonts & colors */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #f7f9fc;
        color: #222222;
    }

    /* Container */
    .main > div {
        max-width: 700px !important;
        margin: 0 auto;
        padding: 2rem 1rem;
        background: white;
        box-shadow: 0 8px 30px rgb(0 0 0 / 0.1);
        border-radius: 12px;
    }

    /* Title */
    h1 {
        font-weight: 700 !important;
        color: #0b3d91;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    /* Subtitle */
    .subtitle {
        font-size: 1.1rem;
        color: #444444;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* File uploader */
    .stFileUploader > div > div > input {
        border-radius: 8px;
        border: 1.5px solid #0b3d91;
        padding: 0.5rem;
    }

    /* Download button */
    div.stDownloadButton > button {
        background-color: #0b3d91;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1.4rem;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }

    div.stDownloadButton > button:hover {
        background-color: #074080;
        cursor: pointer;
    }

    /* Spinner */
    .stSpinner {
        margin: 1rem auto;
        text-align: center;
    }

    /* Footer */
    footer {
        text-align: center;
        font-size: 0.9rem;
        color: #888;
        margin-top: 3rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("📄", unsafe_allow_html=True)
st.title("PDF Compressor & Splitter")
st.markdown(
    '<p class="subtitle">Upload any PDF to compress and split its pages into individual files. Download all pages as a ZIP archive, ready to use.</p>',
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Upload your PDF file here.")

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

    with st.spinner("Compressing and splitting your PDF..."):
        compress_and_split_pdf(input_path, split_folder)
        zip_folder(split_folder, zip_output)

    st.success("✅ Your PDF has been processed successfully!")
    with open(zip_output, "rb") as f:
        st.download_button("⬇️ Download Split ZIP", f, file_name="SplitPDFs.zip")

    shutil.rmtree(working_dir)

else:
    st.info("📤 Please upload a PDF file to get started.")

# Footer
st.markdown(
    """
    <footer>
        Developed by Unmesh • Powered by PyMuPDF & Streamlit
    </footer>
    """,
    unsafe_allow_html=True,
)
