import os
import shutil
from zipfile import ZipFile
import fitz  # PyMuPDF
import streamlit as st
from PIL import Image
import io

# --- Functions ---
def add_watermark(input_path, output_path, watermark_path, scale=0.5, position=(0.5, 0.5), opacity=0.5):
    """Add watermark to PDF with adjustable size, position and opacity"""
    doc = fitz.open(input_path)
    
    # Convert watermark to RGBA if needed
    watermark_img = Image.open(watermark_path)
    if watermark_img.mode != 'RGBA':
        watermark_img = watermark_img.convert('RGBA')
    
    # Create a temporary watermark file
    temp_watermark = "temp_watermark.png"
    watermark_img.save(temp_watermark)
    
    for page in doc:
        # Get page dimensions
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Calculate watermark dimensions based on scale
        wm_width = watermark_img.width * scale
        wm_height = watermark_img.height * scale
        
        # Calculate position (convert from ratio to coordinates)
        x = position[0] * (page_width - wm_width)
        y = position[1] * (page_height - wm_height)
        
        # Create a rectangle for the watermark
        rect = fitz.Rect(x, y, x + wm_width, y + wm_height)
        
        # Add watermark to the page
        page.insert_image(rect, filename=temp_watermark, opacity=opacity)
    
    # Save the watermarked PDF
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    
    # Remove temporary watermark file
    if os.path.exists(temp_watermark):
        os.remove(temp_watermark)

def compress_and_split_pdf(input_path, output_folder, watermark_path=None, scale=0.5, position=(0.5, 0.5), opacity=0.5):
    """Compress and split PDF with optional watermark"""
    doc = fitz.open(input_path)
    os.makedirs(output_folder, exist_ok=True)
    
    for i, page in enumerate(doc):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.set_metadata({})
        
        if watermark_path:
            # Create temporary single-page PDF to watermark
            temp_input = os.path.join(output_folder, f"temp_{i}.pdf")
            temp_output = os.path.join(output_folder, f"temp_wm_{i}.pdf")
            new_doc.save(temp_input)
            
            # Apply watermark
            add_watermark(temp_input, temp_output, watermark_path, scale, position, opacity)
            
            # Clean up temp files
            os.remove(temp_input)
            new_doc = fitz.open(temp_output)
            os.remove(temp_output)
        
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

def show_preview(pdf_path, watermark_path, scale, position, opacity):
    """Show a preview of the first page with watermark"""
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Convert page to image
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    
    # Prepare watermark
    watermark_img = Image.open(watermark_path)
    if watermark_img.mode != 'RGBA':
        watermark_img = watermark_img.convert('RGBA')
    
    # Resize watermark
    wm_width = int(watermark_img.width * scale)
    wm_height = int(watermark_img.height * scale)
    watermark_img = watermark_img.resize((wm_width, wm_height), Image.LANCZOS)
    
    # Calculate position
    x = int(position[0] * (img.width - wm_width))
    y = int(position[1] * (img.height - wm_height))
    
    # Create transparent layer for watermark
    watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark_img, (x, y))
    
    # Adjust opacity
    if opacity < 1.0:
        alpha = watermark_layer.split()[3]
        alpha = alpha.point(lambda p: p * opacity)
        watermark_layer.putalpha(alpha)
    
    # Combine images
    combined = Image.alpha_composite(img.convert('RGBA'), watermark_layer)
    
    # Display preview
    st.image(combined, caption="Watermark Preview (First Page)", use_column_width=True)
    doc.close()

# --- UI Setup ---
st.set_page_config(
    page_title="PDF Watermark Tool",
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

    /* Slider labels */
    .stSlider label {
        font-weight: 500 !important;
    }

    /* Watermark settings section */
    .watermark-settings {
        background: #f0f4f8;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("📄", unsafe_allow_html=True)
st.title("PDF Watermark Tool")
st.markdown(
    '<p class="subtitle">Upload a PDF and add a watermark before compressing and splitting into individual pages.</p>',
    unsafe_allow_html=True,
)

# --- Main App ---
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Upload your PDF file here.")

if uploaded_file:
    # Create working directory
    working_dir = "split_output"
    split_folder = os.path.join(working_dir, "pages")
    zip_output = os.path.join(working_dir, "numbered_pages.zip")
    
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.makedirs(split_folder, exist_ok=True)
    
    # Save uploaded PDF
    input_path = os.path.join(working_dir, "input.pdf")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Watermark settings section
    with st.expander("⚙️ Watermark Settings", expanded=True):
        watermark_file = st.file_uploader(
            "Upload watermark image (PNG recommended)", 
            type=["png", "jpg", "jpeg"],
            help="Use a transparent PNG for best results"
        )
        
        if watermark_file:
            # Save watermark temporarily
            watermark_path = os.path.join(working_dir, "watermark.png")
            with open(watermark_path, "wb") as f:
                f.write(watermark_file.getbuffer())
            
            # Watermark controls
            col1, col2 = st.columns(2)
            with col1:
                scale = st.slider(
                    "Watermark Size", 
                    min_value=0.1, 
                    max_value=2.0, 
                    value=0.5, 
                    step=0.1,
                    help="Adjust the size of the watermark"
                )
                opacity = st.slider(
                    "Watermark Opacity", 
                    min_value=0.1, 
                    max_value=1.0, 
                    value=0.5, 
                    step=0.1,
                    help="How transparent the watermark should be"
                )
            
            with col2:
                x_pos = st.slider(
                    "Horizontal Position", 
                    min_value=0.0, 
                    max_value=1.0, 
                    value=0.5, 
                    step=0.01,
                    help="Left (0.0) to Right (1.0)"
                )
                y_pos = st.slider(
                    "Vertical Position", 
                    min_value=0.0, 
                    max_value=1.0, 
                    value=0.5, 
                    step=0.01,
                    help="Top (0.0) to Bottom (1.0)"
                )
            
            position = (x_pos, y_pos)
            
            # Show preview
            st.markdown("### Preview")
            show_preview(input_path, watermark_path, scale, position, opacity)
    
    # Process button
    if st.button("🚀 Process PDF", use_container_width=True):
        with st.spinner("Processing your PDF..."):
            try:
                if watermark_file:
                    compress_and_split_pdf(
                        input_path, 
                        split_folder, 
                        watermark_path, 
                        scale, 
                        position, 
                        opacity
                    )
                else:
                    compress_and_split_pdf(input_path, split_folder)
                
                zip_folder(split_folder, zip_output)
                st.success("✅ Your PDF has been processed successfully!")
                
                # Download button
                with open(zip_output, "rb") as f:
                    st.download_button(
                        "⬇️ Download Split ZIP", 
                        f, 
                        file_name="Watermarked_PDFs.zip",
                        use_container_width=True
                    )
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
            finally:
                # Clean up
                if os.path.exists(working_dir):
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