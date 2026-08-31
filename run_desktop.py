"""
MailMind AI - Bağımsız Mac Masaüstü Penceresi Başlatıcı
"""
import subprocess
import time
import webview
import sys

def start_streamlit():
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app_ui.py", "--server.headless=true", "--server.port=8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

if __name__ == "__main__":
    process = start_streamlit()
    time.sleep(2.5)  # Sunucunun başlamasını bekle

    # Kendi bağımsız Mac penceresini aç
    window = webview.create_window(
        title="⚡ MailMind AI — Kişisel E-Posta Asistanı",
        url="http://localhost:8501",
        width=1150,
        height=780,
        resizable=True,
        min_size=(900, 600)
    )
    
    webview.start()
    process.terminate()