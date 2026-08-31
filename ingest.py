"""
Garantili ve Temiz Veri İçe Aktarma 
Çok Dilli Embedding Modeli (paraphrase-multilingual-MiniLM-L12-v2)
"""
import os
import sqlite3
import json
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rag_knowledge.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def main():
    print("=" * 55)
    print("📥 E-Posta Veri İçe Aktarma Başlıyor...")
    print("=" * 55)

    # 1. Türkçe desteği güçlü çok dilli embedding modeli
    print("[1/3] Çok dilli embedding modeli yükleniyor...")
    embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # 2. Veritabanını Temizle
    conn = init_database()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM document_chunks")
    conn.commit()

    # 3. Yalnızca mevcut dosyaları tara
    total_chunks = 0
    for filename in sorted(os.listdir(DATA_DIR)):
        if filename.endswith((".txt", ".md")):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()
                paragraphs = [p.strip() for p in raw_content.split("---") if p.strip()]
                if not paragraphs:
                    paragraphs = [p.strip() for p in raw_content.split("\n\n") if p.strip()]

            print(f"\n[*] '{filename}' dosyası işleniyor ({len(paragraphs)} e-posta/parça):")

            for idx, text in enumerate(paragraphs):
                vector = embed_model.encode(text).tolist()

                cursor.execute("""
                    INSERT INTO document_chunks (source_file, chunk_index, content, embedding_json)
                    VALUES (?, ?, ?, ?)
                """, (filename, idx, text, json.dumps(vector)))
                
                total_chunks += 1
                print(f"  -> E-posta {idx+1} kaydedildi.")

    conn.commit()
    conn.close()
    print("\n" + "=" * 55)
    print(f"🎉 BAŞARILI! Toplam {total_chunks} adet e-posta veritabanına kaydedildi.")
    print("=" * 55)

if __name__ == "__main__":
    main()