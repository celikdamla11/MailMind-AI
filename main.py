"""
Uçtan Uca Yerel RAG Asistanı 
Foundry Local + SentenceTransformers + SQLite
"""
import os
import sys
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

def retrieve_top_chunks(query, embed_model, top_k=2):
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

def main():
    print("=" * 60)
    print("🤖 YEREL RAG SORU-CEVAP ASİSTANI BAŞLATILIYOR")
    print("=" * 60)

    # 1. Embedding Modelini Yükle
    print("[1/2] Embedding modeli hazırlanıyor...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    # 2. Foundry Local Chat Modelini Hazırla
    print("[2/2] Foundry Local LLM hazırlanıyor...")
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
        
        config = Configuration(app_name="rag_assistant")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance
        
        model_name = "phi-3.5-mini"
        print(f"[*] '{model_name}' modeli kontrol ediliyor...")
        model = manager.catalog.get_model(model_name)
        
        # İndirilmediyse indir
        print(f"[*] Model dosyaları kontrol ediliyor / indiriliyor...")
        model.download(lambda p: print(f"\r -> İndirme: %{p:.1f}", end="", flush=True))
        print("\n[+] İndirme tamamlandı.")

        # Belleğe yükle
        print("[*] Model belleğe yükleniyor...")
        model.load()
        chat_client = model.get_chat_client()
        print(f"[+] Model başarıyla yüklendi ve hazır!")

    except Exception as e:
        print(f"\n[!] Model başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" Hazır! Şirket rehberinizle ilgili sorularınızı sorabilirsiniz.")
    print(" Çıkmak için 'q' veya 'exit' yazın.")
    print("=" * 60)

    # 3. İnteraktif Soru-Cevap Döngüsü
    while True:
        try:
            query = input("\n[Soru Sor]: ").strip()
            if not query:
                continue
            if query.lower() in ["q", "exit", "cikis", "quit"]:
                print("İyi günler!")
                break

            # A) Retrieve
            top_chunks = retrieve_top_chunks(query, embed_model, top_k=2)
            
            context_text = "\n\n".join([f"[{c['source']}]: {c['content']}" for c in top_chunks])
            sources = list(set([c['source'] for c in top_chunks]))

            # B) Augment
            system_prompt = (
                "Sen yalnızca aşağıda verilen BAĞLAM (Context) bilgilerini kullanarak Türkçe yanıt veren bir kurumsal asistansın.\n"
                "Kurallar:\n"
                "1. Yalnızca verilen metindeki gerçekleri kullan.\n"
                "2. Eğer verilen metinde sorunun cevabı yoksa 'Bu bilgi şirket dokümanlarında bulunmamaktadır.' de.\n"
                "3. Tahminde bulunma veya uydurma."
            )
            
            user_prompt = f"BAĞLAM BİLGİLERİ:\n{context_text}\n\nKULLANICI SORUSU:\n{query}"

            # C) Generate
            response = chat_client.complete_chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            # Yanıt metnini ayıkla
            if hasattr(response, 'text'):
                answer = response.text
            elif hasattr(response, 'choices'):
                answer = response.choices[0].message.content
            else:
                answer = str(response)

            print("\n" + "-" * 50)
            print(f"[Cevap]:\n{answer.strip()}")
            print("-" * 50)
            print(f"📌 Kaynak: {', '.join(sources)}")
            
        except KeyboardInterrupt:
            print("\nProgram sonlandırıldı.")
            break

if __name__ == "__main__":
    main()