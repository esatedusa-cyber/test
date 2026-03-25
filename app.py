import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

st.set_page_config(page_title="Gemini High-Res Tile Refiner", layout="wide")
st.title("🚀 Gemini ile Otomatik Yüksek Çözünürlüklü Görsel Üretici")
st.markdown("Base üret → her bölgeyi zoomed olarak düzelt → 3072x3072 veya daha büyük yap. Tam senin istediğin yöntem!")

with st.sidebar:
    api_key = st.text_input("🔑 Gemini API Key", type="password", help="aistudio.google.com'dan al")
    if api_key:
        genai.configure(api_key=api_key)
    
    model_name = st.selectbox(
        "Model Seç",
        ["gemini-2.5-flash-image", "gemini-3.1-flash-image-preview"],
        index=0,
        help="Image generation ve editing için en iyi modeller"
    )
    
    grid_size = st.slider("Grid Boyutu (3 = 3x3 tile → 3072px)", 2, 5, 3)
    tile_size = st.selectbox("Her Tile'ın Çözünürlüğü", [1024, 1536], index=0)
    overlap = st.slider("Overlap (dikişsizlik için %)", 0.0, 0.30, 0.18)
    
    prompt = st.text_area("📝 Görsel Prompt'un", height=130, 
        value="Futuristik bir cyberpunk şehir gecesi, neon ışıklar, yağmur, çok detaylı, sinematik")

if not api_key:
    st.info("👈 Sidebar'dan Gemini API key'ini gir")
    st.stop()

model = genai.GenerativeModel(model_name)

if st.button("🖼️ YÜKSEK ÇÖZÜNÜRLÜKLÜ GÖRSEL ÜRET (1-4 dakika sürebilir)", type="primary"):
    with st.spinner("Base görsel üretiliyor..."):
        try:
            base_response = model.generate_content(prompt)
            base_image = None
            for part in base_response.candidates[0].content.parts:
                if part.inline_data:
                    base_image = Image.open(io.BytesIO(part.inline_data.data))
                    break
            
            if base_image is None:
                st.error("Base görsel üretilemedi. Farklı prompt dene.")
                st.stop()
            
            base_image = base_image.convert("RGB")
            st.image(base_image, caption="Base Görsel (düşük çözünürlük)", use_column_width=True)
            
            # Tile işleme
            final_size = tile_size * grid_size
            final_image = Image.new("RGB", (final_size, final_size))
            step = int(tile_size * (1 - overlap))
            
            progress_bar = st.progress(0)
            status = st.empty()
            
            total_tiles = grid_size * grid_size
            
            for idx, (row, col) in enumerate([(r, c) for r in range(grid_size) for c in range(grid_size)]):
                status.text(f"Tile {row+1}x{col+1} işleniyor... ({idx+1}/{total_tiles})")
                
                # Base'ten bölgeyi kes
                x = col * (base_image.width // grid_size)
                y = row * (base_image.height // grid_size)
                cropped = base_image.crop((x, y, x + base_image.width//grid_size, y + base_image.height//grid_size))
                
                # Zoom simülasyonu (düşük kaliteli, tam senin ekran görüntüsü gibi)
                zoomed = cropped.resize((tile_size, tile_size), Image.NEAREST)
                
                fix_prompt = f"""
Bu görsel, orijinal AI görselinin {row+1}x{col+1} bölgesinin yakınlaştırılmış (zoomed) ve kalitesi düşürülmüş halidir.
Tüm pikselasyon, bulanıklık, artefakt ve kalite kaybını tamamen gider.
Çok yüksek detaylı, keskin, profesyonel kalitede yeni versiyon üret.
Orijinal prompt'taki stil, renkler, kompozisyon ve atmosferle %100 uyumlu olsun.
                """
                
                tile_response = model.generate_content([fix_prompt, zoomed])
                
                tile_img = None
                for part in tile_response.candidates[0].content.parts:
                    if part.inline_data:
                        tile_img = Image.open(io.BytesIO(part.inline_data.data))
                        break
                
                if tile_img:
                    paste_x = col * step
                    paste_y = row * step
                    final_image.paste(tile_img.resize((tile_size, tile_size)), (paste_x, paste_y))
                
                progress_bar.progress((idx + 1) / total_tiles)
                time.sleep(0.3)  # Rate limit koruması
            
            st.success(f"✅ Tamamlandı! {final_size}×{final_size} piksel yüksek çözünürlüklü görsel hazır")
            st.image(final_image, caption="Final Yüksek Çözünürlüklü Görsel", use_column_width=True)
            
            # İndir butonu
            buf = io.BytesIO()
            final_image.save(buf, format="PNG")
            st.download_button(
                label="📥 Yüksek Çözünürlüklü Görseli İndir",
                data=buf.getvalue(),
                file_name="high_res_final.png",
                mime="image/png"
            )
            
        except Exception as e:
            st.error(f"Hata: {str(e)}")
            st.info("API key'in geçerli mi? Model image generation destekliyor mu? Kontrol et.")

st.caption("Not: Ücretsiz Gemini API tier'ında günlük limit olabilir. Yoğun kullanım için billing aç.")
