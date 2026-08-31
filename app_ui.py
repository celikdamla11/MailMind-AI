
import os
import sqlite3
import json
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rag_knowledge.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

st.set_page_config(
    page_title="MailMind AI",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #F8F4FA !important; /* Açık Lila / Lavanta Zemin */
    }

    /* Sol Sidebar Lila Dokunuş */
    [data-testid="stSidebar"] {
        background-color: #F1EBF5 !important;
        border-right: 1px solid #E4D9EB !important;
    }

    /* O Beğendiğiniz Mor/İndigo/Pembe Degrade Banner */
    .hero-banner-purple {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 40%, #A855F7 70%, #EC4899 100%);
        padding: 26px 30px;
        border-radius: 22px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px -5px rgba(124, 58, 237, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .hero-desc {
        font-size: 0.95rem;
        color: #EDE9FE;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .badge-pill-purple {
        background: rgba(255, 255, 255, 0.22);
        backdrop-filter: blur(10px);
        padding: 4px 14px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.35);
    }

    /* Sol Panel Lila Kutu */
    .sidebar-info-purple {
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid #DDD0E8;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 16px;
    }
    
    /* Seçili (aktif) sekmenin çerçevesi */
    button[data-baseweb="tab"][aria-selected="true"] {
        border: 2px solid #A855F7 !important;
        border-radius: 10px !important;
        background: #EDE9FE !important;
        color: #7C3AED !important;
    }
</style>
""", unsafe_allow_html=True)

# Modelleri Belleğe Yükle
@st.cache_resource
def load_models():
    embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    from foundry_local_sdk import Configuration, FoundryLocalManager
    config = Configuration(app_name="email_rag_ui")
    try:
        manager = FoundryLocalManager.instance
        if manager is None:
            FoundryLocalManager.initialize(config)
            manager = FoundryLocalManager.instance
    except Exception:
        try:
            FoundryLocalManager.initialize(config)
        except Exception:
            pass
        manager = FoundryLocalManager.instance
    
    model = manager.catalog.get_model("phi-3.5-mini")
    model.download()
    model.load()
    chat_client = model.get_chat_client()
    return embed_model, chat_client

def cosine_similarity(vec_a, vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve_top_chunks(query, embed_model, category_filter=None, top_k=4):
    query_vector = embed_model.encode(query).tolist()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if category_filter and category_filter != "Tümü":
        cursor.execute("SELECT source_file, content, embedding_json FROM document_chunks WHERE source_file = ?", (category_filter,))
    else:
        cursor.execute("SELECT source_file, content, embedding_json FROM document_chunks")
        
    rows = cursor.fetchall()
    conn.close()

    scored = []
    for source_file, content, embedding_json in rows:
        chunk_vec = json.loads(embedding_json)
        score = cosine_similarity(query_vector, chunk_vec)
        scored.append({"source": source_file, "content": content, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

# --- ÜST HERO MOR DEGRADE BANNER ---
st.markdown("""
<div class="hero-banner-purple">
    <div class="hero-title">MailMind AI</div>
    <div class="hero-desc">
        Kişisel Yerel E-Posta & Gelen Kutusu Asistanı 
        <span class="badge-pill-purple">🔒 %100 ÇEVRİMDIŞI & GİZLİ</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SOL MENÜ ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-info-purple">
        <b style="color:#6D28D9;">⚡ MailMind Panel</b><br>
        <span style="font-size:0.85rem; color:#4B5563;">E-postalarınız cihazınızdaki yerel <b>Phi-3.5</b> modeliyle güvenle taranır.</span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🎯 Arama Kapsamı")
    category_options = {
        " Tüm Gelen Kutusu": "Tümü",
        "🎓 Akademik & Dersler": "academic.txt",
        "💼 Kariyer & Mülakatlar": "career.txt",
        "🧾 Faturalar & Ödemeler": "invoices.txt",
        "📦 Kargo & Siparişler": "orders.txt",
        "📌 Diğer E-Postalar": "other.txt"
    }
    selected_label = st.selectbox("Aranacak Alan:", list(category_options.keys()))
    selected_filter = category_options[selected_label]

    st.markdown("---")
    st.markdown("**💡 Hızlı Örnek Sorular:**")
    st.markdown("• *Kargo takip numaram nedir?*")
    st.markdown("• *Staj mülakatım saat kaçta?*")
    st.markdown("• *Bu ayki faturalarım ne kadar?*")

with st.spinner("💜 Yapay zeka başlatılıyor..."):
    embed_model, chat_client = load_models()

# --- SEKMELER ---
tab_chat, tab_categories, tab_stats = st.tabs(["💬 Asistan ile Sohbet", "📂 Gelen Kutusu", "📊 Sistem İstatistikleri"])

# 1. SOHBET
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Merhaba! Ben **MailMind AI**. Gelen kutunuzdaki e-postalar tamamen yerel olarak indekslendi. Hangi e-postanızı bulmamı veya özetlememi istersiniz?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input(f"{selected_label} hakkında soru sorun..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("🔍 E-postalarınız taranıyor..."):
                top_chunks = retrieve_top_chunks(user_query, embed_model, category_filter=selected_filter, top_k=4)
                context_text = "\n\n".join([f"[{c['source']}]: {c['content']}" for c in top_chunks])
                sources = list(set([c['source'] for c in top_chunks]))

                system_prompt = (
                    "Sen kullanıcının kişisel e-postalarını tarayan akıllı ve samimi bir asistansın (MailMind AI).\n"
                    "Kurallar:\n"
                    "1. Yalnızca verilen BAĞLAM e-postalarındaki gerçek bilgilere göre net ve Türkçe yanıt ver.\n"
                    "2. Tarihleri, para miktarlarını veya bağlantı linklerini net şekilde vurgula.\n"
                    "3. Eğer aranan bilgi e-postalarda yoksa 'Bu bilgiye gelen e-postalarınızda ulaşılamadı.' de."
                )
                user_prompt = f"BAĞLAM (E-POSTALAR):\n{context_text}\n\nKULLANICI SORUSU:\n{user_query}"

                response = chat_client.complete_chat([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ])
                
                answer = response.choices[0].message.content if hasattr(response, 'choices') else getattr(response, 'text', str(response))

                st.markdown(answer)
                if sources:
                    st.caption(f"📌 **Kaynak:** `{', '.join(sources)}`")

                with st.expander("🔍 Eşleşen E-Posta Detayını Gör"):
                    for chunk in top_chunks:
                        st.write(f"**Dosya:** `{chunk['source']}` (Benzerlik Skoru: `{chunk['score']:.4f}`)")
                        st.text(chunk["content"])

        st.session_state.messages.append({"role": "assistant", "content": answer})

# 2. SEVDİĞİNİZ RENGARENK GELEN KUTUSU KARTLARI
with tab_categories:
    st.subheader("📬 Kategorilere Göre E-Postalarınız")

    col1, col2 = st.columns(2)
    categories_list = [
        ("🎓 Akademik & Okul", "academic.txt", "#EDE9FE", "#6D28D9"),       # Canlı Mor
        ("💼 Kariyer & Mülakatlar", "career.txt", "#E0F2FE", "#0369A1"),    # Canlı Mavi
        ("🧾 Faturalar & Ödemeler", "invoices.txt", "#FCE7F3", "#BE185D"),  # Canlı Pembe
        ("📦 Sipariş & Kargo", "orders.txt", "#FEF3C7", "#B45309"),         # Canlı Sarı/Turuncu
        ("📌 Diğer E-Postalar", "other.txt", "#F3F4F6", "#374151")          # Şık Gri
    ]

    for idx, (cat_name, cat_file, bg_color, text_color) in enumerate(categories_list):
        filepath = os.path.join(DATA_DIR, cat_file)
        target_col = col1 if idx % 2 == 0 else col2
        
        with target_col:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                if content:
                    emails = [e.strip() for e in content.split("---") if e.strip()]
                    st.markdown(f"""
                    <div style="background-color:{bg_color}; color:{text_color}; padding:14px; border-radius:14px; margin-bottom:8px; font-weight:700; border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
                        {cat_name} ({len(emails)} e-posta)
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for e_idx, em in enumerate(emails, 1):
                        lines = em.split("\n")
                        subject = lines[1] if len(lines) > 1 else lines[0]
                        with st.expander(f"✉️ {subject[:45]}..."):
                            st.text(em)
                else:
                    st.info(f"{cat_name} kategorisinde henüz mail yok.")

# 3. İSTATİSTİKLER
with tab_stats:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    total_chunks = cursor.fetchone()[0]
    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("İndekslenen E-Posta Parçası", f"{total_chunks} Adet")
    c2.metric("Yerel Yapay Zeka Modeli", "Phi-3.5-mini")
    c3.metric("Gizlilik Durumu", "%100 Çevrimdışı")