
import os
import sys
import time
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rag_knowledge.db")

def cosine_similarity(vec_a, vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve_top_chunks(query, embed_model, top_k=4):
    query_vector = embed_model.encode(query).tolist()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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

def answer_query(user_query, embed_model, chat_client):
    top_chunks = retrieve_top_chunks(user_query, embed_model, top_k=4)
    context_text = "\n\n".join([f"[{c['source']}]: {c['content']}" for c in top_chunks])
    sources = list(set([c['source'] for c in top_chunks]))

    system_prompt = (
        "Sen kullanıcının gelen kutusundaki e-postaları tarayıp soruları yanıtlayan kişisel bir asistansın.\n"
        "Kurallar:\n"
        "1. Yalnızca verilen BAĞLAM e-postalarındaki gerçek bilgilere göre net ve Türkçe cevap ver.\n"
        "2. Eğer aranan bilgi e-postalarda yoksa 'Bu bilgiye gelen e-postalarınızda ulaşılamadı.' de.\n"
        "3. Tahminde bulunma veya uydurma."
    )
    user_prompt = f"BAĞLAM (E-POSTALAR):\n{context_text}\n\nKULLANICI SORUSU:\n{user_query}"

    response = chat_client.complete_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    answer = response.choices[0].message.content if hasattr(response, 'choices') else getattr(response, 'text', str(response))
    return answer.strip(), sources

TEST_CASES = [
    {
        "id": 1,
        "kategori": "💼 Kariyer / Staj",
        "soru": "Staj mülakatım ne zaman ve hangi platformda yapılacak?",
        "beklenen_anahtarlar": ["30 Ekim", "Teams"],
    },
    {
        "id": 2,
        "kategori": "🧾 Faturalar",
        "soru": "İnternet faturamın tutarı ne kadar ve son ödeme tarihi nedir?",
        "beklenen_anahtarlar": ["420", "24 Ekim"],
    },
    {
        "id": 3,
        "kategori": "📦 Siparişler",
        "soru": "Kargo takip numaram nedir?",
        "beklenen_anahtarlar": ["ARAS-789456123", "789456123"],
    },
    {
        "id": 4,
        "kategori": "🎓 Akademik",
        "soru": "Ahmet Hoca CENG101 projesinin teslimini hangi tarihe erteledi?",
        "beklenen_anahtarlar": ["28 Aralık"],
    },
    {
        "id": 5,
        "kategori": "🛑 Negatif Test (Halüsinasyon Önleme)",
        "soru": "Uçak biletim hangi havalimanından kalkıyor?",
        "beklenen_anahtarlar": ["ulaşılamadı", "bulunmamaktadır", "yok", "bilgi"],
    }
]

def main():
    print("=" * 70)
    print("🧪 YEREL RAG E-POSTA ASİSTANI - OTOMATİK SİSTEM DEĞERLENDİRME TESTİ")
    print("=" * 70)

    print("\n[*] Test ortamı hazırlanıyor...")
    embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    from foundry_local_sdk import Configuration, FoundryLocalManager
    config = Configuration(app_name="rag_eval")
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

    # Modeli hazırla ve indir
    model_name = "phi-3.5-mini"
    print(f"[*] '{model_name}' modeli kontrol ediliyor (ilk çalıştırmada indirilebilir)...")
    model = manager.catalog.get_model(model_name)
    model.download(lambda p: print(f"\r -> İlerleme: %{p:.1f}", end="", flush=True))
    print("\n[+] Model indirildi, belleğe yükleniyor...")
    model.load()
    chat_client = model.get_chat_client()
    print("[+] Modeller hazır! Testler başlıyor...\n")

    # Testleri Koştur
    basarili_sayisi = 0
    toplam_sure = 0

    for test in TEST_CASES:
        print("-" * 70)
        print(f"📋 [Test #{test['id']}] Kategori: {test['kategori']}")
        print(f"❓ Soru: '{test['soru']}'")
        
        start_time = time.time()
        answer, sources = answer_query(test["soru"], embed_model, chat_client)
        elapsed = time.time() - start_time
        toplam_sure += elapsed

        gecerli = any(key.lower() in answer.lower() for key in test["beklenen_anahtarlar"])
        
        print(f"⏱️ Yanıt Süresi: {elapsed:.2f} saniye")
        print(f"📌 Bulunan Kaynaklar: {sources}")
        print(f"💬 Model Yanıtı:\n   > {answer}")

        if gecerli:
            print("✅ Sonuç: BAŞARILI (Doğru bilgi tespit edildi)")
            basarili_sayisi += 1
        else:
            print("⚠️ Sonuç: İNCELEME GEREKLİ")

    # Skor Tablosu
    print("\n" + "=" * 70)
    print("📊 DEĞERLENDİRME VE BAŞARI RAPORU")
    print("=" * 70)
    print(f"🎯 Toplam Test: {len(TEST_CASES)}")
    print(f"✅ Başarılı Test: {basarili_sayisi} / {len(TEST_CASES)}")
    print(f"📈 Doğruluk Oranı: %{(basarili_sayisi / len(TEST_CASES)) * 100:.1f}")
    print(f"⚡ Ortalama Yanıt Hızı: {(toplam_sure / len(TEST_CASES)):.2f} saniye / soru")
    print("=" * 70)

if __name__ == "__main__":
    main()