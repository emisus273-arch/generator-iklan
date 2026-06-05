import streamlit as st
from PIL import Image
from gtts import gTTS
import os
from rembg import remove
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip

# ---------------------------------------------------------
# FUNGSI ASSISTANT: AUTO CROP 9:16
# ---------------------------------------------------------
def ubah_rasio_9_16(img):
    w, h = img.size
    target_ratio = 9 / 16
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(target_ratio * h)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return img.resize((720, 1280), Image.Resampling.LANCZOS)

# ---------------------------------------------------------
# KONFIGURASI STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="AI Super Affiliate Video Generator", layout="wide")
st.title("🚀 AI Automated Video Ad Generator (V5 - God Mode)")

# --- SIDEBAR KONTROL ---
st.sidebar.header("🎨 Pengaturan Visual & Audio")
warna_teks = st.sidebar.selectbox("Warna Subtitle", ["#FFFF00", "#FFFFFF", "#00FF00"], format_func=lambda x: "Kuning" if x=="#FFFF00" else ("Putih" if x=="#FFFFFF" else "Hijau"))
ukuran_font = st.sidebar.slider("Ukuran Font", 30, 70, 45)
skala_produk = st.sidebar.slider("Ukuran Produk (%)", 25, 60, 35) / 100
posisi_y_teks = st.sidebar.slider("Tinggi Subtitle", 100, 300, 180)
volume_bgm = st.sidebar.slider("Volume Musik Latar", 0.05, 0.30, 0.15, step=0.05)

st.sidebar.markdown("---")
api_key = st.sidebar.text_input("Gemini API Key (Opsional)", type="password")

# --- PANEL UTAMA ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. AI Copywriting")
    nama_prod = st.text_input("Nama Produk:", "Kemeja Oversize Linen")
    keunggulan_prod = st.text_input("Keunggulan:", "Bahan adem, tidak mudah kusut")
    gaya_bahasa = st.selectbox("Gaya Bahasa:", ["Hard Sell / Diskon", "Storytelling / Solusi"])
    
    if st.button("🪄 Hasilkan Skrip", use_container_width=True):
        st.session_state['skrip_final'] = f"Guys! {nama_prod} lagi viral banget karena {keunggulan_prod}. Buruan klik keranjang kuning sekarang!"
    
    default_text = st.session_state.get('skrip_final', "Produk premium ini lagi diskon besar-besaran, klik keranjang kuning sekarang!")
    teks_iklan = st.text_area("Konfirmasi Skrip:", value=default_text, height=100)

with col2:
    st.subheader("2. Unggah Aset")
    model_file = st.file_uploader("Foto Model / Background", type=['png', 'jpg', 'jpeg'])
    product_file = st.file_uploader("Foto Produk", type=['png', 'jpg', 'jpeg'])
    bgm_file = st.file_uploader("Musik Latar / BGM (Opsional .mp3)", type=['mp3'])

st.markdown("---")

# --- PROSES RENDER ---
if st.button("🎬 Mulai Render Video", use_container_width=True):
    if model_file and product_file and teks_iklan:
        with st.spinner("AI sedang merender video iklan Anda..."):
            try:
                # 1. Olah Gambar
                img_model = ubah_rasio_9_16(Image.open(model_file).convert("RGBA"))
                produk_nobg = remove(Image.open(product_file)).convert("RGBA")
                
                # Tempel Produk
                t_w = int(img_model.width * skala_produk)
                t_h = int(produk_nobg.height * (t_w / produk_nobg.width))
                produk_resized = produk_nobg.resize((t_w, t_h), Image.Resampling.LANCZOS)
                img_model.paste(produk_resized, (img_model.width - t_w - 40, img_model.height - t_h - 120), produk_resized)
                
                temp_img_path = "final_frame.jpg"
                img_model.convert('RGB').save(temp_img_path)
                st.image(img_model, width=300, caption="Preview Layout 9:16")
                
                # 2. Generate Voiceover
                tts = gTTS(text=teks_iklan, lang='id', slow=False)
                tts.save("vo.mp3")
                vo_clip = AudioFileClip("vo.mp3")
                total_duration = vo_clip.duration
                
                # 3. Mixing Audio (Voiceover + BGM)
                audio_targets = [vo_clip]
                if bgm_file:
                    with open("temp_bgm.mp3", "wb") as f:
                        f.write(bgm_file.getbuffer())
                    # Potong BGM sewajarnya video dan kecilkan volumenya otomatis
                    bgm_clip = AudioFileClip("temp_bgm.mp3").subclip(0, total_duration).volumex(volume_bgm)
                    audio_targets.append(bgm_clip)
                
                final_audio = CompositeAudioClip(audio_targets)
                
                # 4. Buat Video & Subtitle
                base_video = ImageClip(temp_img_path).set_duration(total_duration)
                words = teks_iklan.split()
                chunks = [' '.join(words[i:i+4]) for i in range(0, len(words), 4)]
                dur_chunk = total_duration / len(chunks)
                
                subtitle_clips = []
                curr_time = 0
                for chunk in chunks:
                    txt = TextClip(chunk, fontsize=ukuran_font, color=warna_teks, bg_color='rgba(0,0,0,0.6)', font='Arial-Bold', method='caption', size=(base_video.w * 0.85, None))
                    txt = txt.set_position(('center', base_video.h - posisi_y_teks)).set_start(curr_time).set_duration(dur_chunk)
                    subtitle_clips.append(txt)
                    curr_time += dur_chunk
                
                # 5. Export MP4
                final_video = CompositeVideoClip([base_video] + subtitle_clips).set_audio(final_audio)
                output_path = "iklan_god_mode.mp4"
                final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                
                final_video.close()
                vo_clip.close()
                if bgm_file: bgm_clip.close()
                
                st.success("🎉 Video Berhasil Dibuat!")
                st.video(output_path)
                with open(output_path, "rb") as file:
                    st.download_button(label="📥 Download Video Iklan", data=file, file_name="Iklan_Affiliate_BGM.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"Sistem Error: {e}")
