# ⚡ MailMind AI — Kişisel Yerel E-Posta & Gelen Kutusu Asistanı

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Framework](https://img.shields.io/badge/Foundry%20Local-Phi--3.5--mini-purple.svg)
![Database](https://img.shields.io/badge/Vector%20Store-SQLite-green.svg)
![UI](https://img.shields.io/badge/Frontend-Streamlit%20%2B%20PyWebView-pink.svg)
![License](https://img.shields.io/badge/Privacy-100%25%20Offline%20%26%20Local-success.svg)

**MailMind AI**, kullanıcının Gmail gelen kutusundaki e-postaları güvenli bir şekilde yerel ortamına çeken, anlamsal olarak kategorilere ayıran ve **Microsoft Foundry Local** altyapısıyla **%100 çevrimdışı (offline)** olarak soru-cevap imkanı sunan bir **RAG (Retrieval-Augmented Generation)** masaüstü yapay zeka asistanıdır.

---

## 🌟 Öne Çıkan Özellikler

- 🔒 **%100 Gizlilik ve Çevrimdışı Çalışma:** E-postalarınız üçüncü taraf bulut sunucularına (OpenAI vb.) asla gönderilmez; çıkarım ve arama tamamen cihazınızın donanımında gerçekleşir.
- 📬 **Otomatik Akıllı Kategorilendirme:** Gelen e-postalar içeriklerine göre Akademik, Kariyer, Fatura, Sipariş, Diğer ve Gerçek Mailler olarak ayrıştırılır.
- 🔍 **Çok Dilli Anlamsal Arama (Semantic Retrieval):** `paraphrase-multilingual-MiniLM-L12-v2` embedding modeli sayesinde anahtar kelimeye bağımlı kalmadan cümlenin anlamına göre ilgili e-postaları bulur.
- 💬 **Gelişmiş Yerel LLM Entegrasyonu:** `Microsoft Phi-3.5-mini` yerel modeli yalnızca sağlanan bağlamı kullanarak halüsinasyonsuz, net ve kaynak referanslı Türkçe yanıtlar üretir.
- 🖥️ **Bağımsız macOS Masaüstü Penceresi:** Web tarayıcısı sekmesine bağımlı kalmadan `pywebview` ile bağımsız bir masaüstü uygulaması olarak çalışır.
- 🧪 **Otomatik Değerlendirme & Test:** `eval_test.py` ile doğruluk oranını ve yanıt gecikmesini ölçen test paketi barındırır.

---

## 🏗️ Sistem Mimarisi ve Veri Akışı

[ Gmail IMAP API ] │ (fetch_gmail.py) ▼ [ data/ Klasörü ] ── (academic.txt, career.txt, invoices.txt, orders.txt, other.txt, real_mails.txt) │ ▼ (ingest.py - SentenceTransformers Embedding) [ SQLite Vektör Deposu (rag_knowledge.db) ] │ ├──► [ app_ui.py / main.py ] (Kullanıcı Sorusu + Cosine Similarity Top-K Retrieval) │ │ │ ▼ (Augment: İlgili E-posta Bağlamı) │ [ Foundry Local - Phi-3.5-mini ] │ │ │ ▼ (Generate) └──► [ 🖥️ Modern Masaüstü UI (PyWebView) / Terminal Yanıtı ]

---

## 📂 Proje Dizin Yapısı ve Dosyaların Görevleri

```text
FlRAGProject/
├── data/                       # E-posta veri havuzu
│   ├── academic.txt            # Okul, ders ve sınav mailleri
│   ├── career.txt              # Staj, iş ve mülakat davetleri
│   ├── invoices.txt            # Fatura, makbuz ve abonelikler
│   ├── orders.txt              # Kargo takip ve sipariş bildirimleri
│   ├── other.txt               # Diğer / genel e-postalar
│   └── real_mails.txt          # Gmail'den çekilen gerçek e-postalar
├── .venv/                      # Python sanal ortamı
├── fetch_gmail.py              # Gmail'den mailleri çekip kategorilere ayıran betik
├── ingest.py                   # E-postaları vektörleştirip SQLite'a kaydeden veri hattı
├── app_ui.py                   # Streamlit tabanlı modern lila temalı Web Arayüzü
├── run_desktop.py              # Uygulamayı bağımsız bir Mac penceresi olarak açan başlatıcı
├── main.py                     # Terminal üzerinden çalışan RAG komut satırı uygulaması
├── eval_test.py                # Sistemin doğruluk ve hızını ölçen otomatik test betiği
├── start_app.sh                # Mac Automator için tek tıkla başlatma kabuk betiği
├── rag_knowledge.db            # SQLite ilişkisel vektör veritabanı
├── requirements.txt            # Gerekli Python paketleri listesi
└── README.md                   # Proje dokümantasyonu