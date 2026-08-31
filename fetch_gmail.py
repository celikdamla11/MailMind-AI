"""
MailMind AI - Gmail E-Posta Çekme ve Otomatik Sınıflandırma Betiği 
"""
import os
import imaplib
import email
from email.header import decode_header

GMAIL_USER = "kullanici_adiniz@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # 16 haneli Google Uygulama Şifresi

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(str(part))
    return "".join(result)

def auto_categorize(subject, body, sender):
    """E-postayı anahtar kelimelere ve gönderene göre akıllıca kategorilere ayırır."""
    text = (subject + " " + body + " " + sender).lower()
    
    # 1. Faturalar & Ödemeler
    if any(k in text for k in ["fatura", "ödeme", "dekont", "tutar", "son ödeme", "makbuz", "invoice", "receipt", "abonelik"]):
        return "invoices.txt"
    
    # 2. Kargo & Siparişler
    elif any(k in text for k in ["kargo", "sipariş", "teslimat", "takip no", "kurye", "order", "shipped", "tracking", "aras", "yurtiçi", "trendyol", "hepsiburada", "amazon"]):
        return "orders.txt"
    
    # 3. Kariyer & Staj & Mülakat
    elif any(k in text for k in ["staj", "mülakat", "başvuru", "ik@", "insan kaynakları", "kariyer", "interview", "linkedin", "iş teklifi", "hackathon"]):
        return "career.txt"
    
    # 4. Akademik & Üniversite
    elif any(k in text for k in ["ödev", "vize", "final", "sınav", "üniversite", "prof.", "dr.", "ders", "ceng", "moodle", "öğrenci işleri", "kampüs", "fakülte"]):
        return "academic.txt"
    
    # 5. Diğer / Genel
    else:
        return "other.txt"

def fetch_and_categorize_emails(limit=30):
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"[*] Gmail'e bağlanılıyor ({GMAIL_USER})...")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD.replace(" ", ""))
        mail.select("inbox")
        print("[+] Bağlantı başarılı! Son mailler taranıyor...")

        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()
        latest_ids = mail_ids[-limit:]

        categories = {
            "academic.txt": [],
            "career.txt": [],
            "invoices.txt": [],
            "orders.txt": [],
            "other.txt": []
        }

        for m_id in reversed(latest_ids):
            status, data = mail.fetch(m_id, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_mime_header(msg.get("Subject", "Konusuz"))
                    sender = decode_mime_header(msg.get("From", "Bilinmeyen"))
                    date = msg.get("Date", "")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors="ignore")
                                    break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")

                    body = body.strip()
                    if body:
                        cat_file = auto_categorize(subject, body, sender)
                        
                        email_entry = (
                            f"Kimden: {sender}\n"
                            f"Konu: {subject}\n"
                            f"Tarih: {date}\n\n"
                            f"{body[:1200]}\n"
                        )
                        categories[cat_file].append(email_entry)
                        print(f"  -> [{cat_file.replace('.txt', '').upper()}] {subject[:40]}...")

        for filename, emails_list in categories.items():
            if emails_list:
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n---\n\n".join(emails_list))
                print(f"[+] {len(emails_list)} e-posta -> '{filename}' içine yazıldı.")

        mail.close()
        mail.logout()
        print("\n🎉 Tüm e-postalar başarıyla kategorilere ayrıldı!")

    except Exception as e:
        print(f"[!] Hata: {e}")

if __name__ == "__main__":
    fetch_and_categorize_emails(limit=30)