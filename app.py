import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Sayfa ayarları ve otomatik yenileme (10 saniye - diğer veriler için)
st.set_page_config(page_title="Canlı Dashboard (Gece Modu)", layout="wide")
st_autorefresh(interval=10000, key="data_refresh")

headers = {"User-Agent": "Mozilla/5.0"}

if "last_quake_list" not in st.session_state:
    st.session_state.last_quake_list = []

# Gece Modu Stil ve Özelleştirmeler (Üst Bar Ortalandı)
st.markdown("""
    <style>
    /* Genel Arkaplan ve Yazı Rengi */
    body, .main, .stApp {
        background-color: #000000; /* Tam siyah zemin */
        color: #C9D1D9; /* Açık gri yazı rengi */
    }

    /* Panel Stili */
    .panel {
        background-color: #161B22; /* Koyu gri panel arkaplanı */
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
    }

    /* Panel Başlıkları */
    .panel h3 {
        font-size: 18px;
        color: #F5F5F5; /* Daha açık gri başlık rengi */
        margin-bottom: 15px;
    }

    /* Panel İçindeki Liste Öğeleri */
    .item {
        margin: 6px 0;
        font-size: 15px;
        color: #CCCCCC; /* Normal gri öğe rengi */
    }

    /* Deprem Büyüklüğü Vurgu */
    .highlight {
        font-size: 22px;
        color: #FF4B4B; /* Kırmızımsı vurgu rengi */
        font-weight: bold;
    }

    /* Canlı Saat Stili (Üst Barda Konumlandırıldı ve Hizalandı) */
    .clock {
        font-size: 48px; /* Büyük font boyutu */
        font-weight: bold;
        color: #00FF99; /* Parlak yeşil saat rengi */
        /* Üst barda olduğu için margin ve padding ayarları yapıldı */
        margin-top: 0;
        margin-bottom: 0;
        padding-top: 10px; /* Üst boşluk */
        padding-bottom: 10px; /* Alt boşluk */
        text-align: center; /* Ortadaki blok içinde ortala */
        width: 100%; /* Kolon genişliğinin tamamını kullan */
        display: flex; /* İçeriği ortalamak için flexbox kullan */
        justify-content: center; /* Yatayda ortala */
        align-items: center; /* Dikeyde ortala */
        min-height: 50px; /* top-info-value ile aynı minimum yükseklik */
    }

    /* Üst Bilgi Değerleri Stili (Tarih, Hava, Döviz) - Hizalama İçin Flexbox Kullanıldı */
    .top-info-value {
        font-size: 18px; /* Punto Büyütüldü */
        display: flex; /* İçeriği hizalamak için flexbox kullan */
        justify-content: center; /* Yatayda ortala */
        align-items: center; /* Dikeyde ortala */
        min-height: 50px; /* Minimum yükseklik belirleyerek dikey hizalamayı iyileştir */
        text-align: center; /* Metni div içinde ortala (flexbox ile birlikte çalışır) */
    }

    /* Kaydırılabilir Panel İçeriği */
    .scrollable-panel-content {
        max-height: 300px; /* Maksimum yükseklik */
        overflow-y: auto; /* Dikey kaydırmayı etkinleştir */
        padding-right: 10px; /* Kaydırma çubuğu için boşluk */
    }

    /* Kaydırma Çubuğu Stilleri (Webkit tabanlı tarayıcılar için) */
    .scrollable-panel-content::-webkit-scrollbar {
        width: 8px;
    }
    .scrollable-panel-content::-webkit-scrollbar-track {
        background: #161B22; /* Panel arkaplanı ile uyumlu iz */
    }
    .scrollable-panel-content::-webkit-scrollbar-thumb {
        background: #30363D; /* Daha koyu başparmak rengi */
        border-radius: 4px;
    }
    .scrollable-panel-content::-webkit-scrollbar-thumb:hover {
        background: #4F5861; /* Üzerine gelindiğinde daha koyu */
    }

    /* Streamlit'in varsayılan boşluklarını azaltmak veya ayarlamak isterseniz */
     div.block-container {
        padding-top: 1rem; # İhtiyaca göre ayarla
        padding-bottom: 0rem; # İhtiyaca göre ayarla
        padding-left: 1rem; # İhtiyaca göre ayarla
        padding-right: 1rem; # İhtiyaca göre ayarla
    }

    </style>
""", unsafe_allow_html=True)

# === ÜST PANEL (Ortalanmış: Saat, Tarih, Hava Durumu, Döviz) ===
# Kenarlara boşluk bırakarak ortalama yapmak için sütunlar kullanıldı.
# [Boşluk, Saat, Tarih, Hava Durumu, Döviz, Boşluk]
# Oranlar ayarlanarak ortalamanın hassasiyeti belirlenir.
col_spacer_left, col_clock, col_date, col_weather, col_currency, col_spacer_right = st.columns([1, 2, 3, 3, 3, 1]) # Oranlar ayarlandı

with col_clock:
    # Canlı Saat buraya, ortalanacak blok içinde yer alıyor
    st.markdown(f"<div class='clock' id='live-clock'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
    st.markdown("""
        <script>
        function updateLiveClock() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const timeString = `${hours}:${minutes}:${seconds}`;
            const clockElement = document.getElementById('live-clock');
            if (clockElement) {
                clockElement.innerText = timeString;
            }
        }
        updateLiveClock();
        setInterval(updateLiveClock, 1000);
        </script>
    """, unsafe_allow_html=True) # JavaScript kodu da aynı sütunda çalıştırılıyor


with col_date:
    # Tarih değeri, ortalanacak blok içinde yer alıyor
    st.markdown(f"<div class='top-info-value'>{datetime.now().strftime('%d %B %Y')}</div>", unsafe_allow_html=True)


with col_weather:
    # Hava durumu değeri, ortalanacak blok içinde yer alıyor
    try:
        t = requests.get("https://api.open-meteo.com/v1/forecast?latitude=41.01&longitude=28.96&current_weather=true&timezone=Europe%2FIstanbul").json()
        st.markdown(f"<div class='top-info-value'>📍 İstanbul: {t['current_weather']['temperature']}°C, Rüzgar: {t['current_weather']['windspeed']} km/s</div>", unsafe_allow_html=True)
    except:
        st.warning("Hava verisi alınamadı.")

with col_currency:
    # Döviz değeri, ortalanacak blok içinde yer alıyor
    try:
        soup = BeautifulSoup(requests.get("https://www.doviz.com/", headers=headers).text, "html.parser")
        dolar = soup.find("span", {"data-socket-key": "USD"}).text.strip()
        euro = soup.find("span", {"data-socket-key": "EUR"}).text.strip()
        st.markdown(f"<div class='top-info-value'>💵 **Dolar:** {dolar} ₺ &nbsp;&nbsp; 💶 **Euro:** {euro} ₺</div>", unsafe_allow_html=True)
    except:
        st.warning("Döviz verisi alınamadı.")

# Boşluk sütunlarına içerik eklemeye gerek yok

st.markdown("---") # Üst bar ile alt paneller arasına ayırıcı çizgi

# === Veri Çekme Fonksiyonları ===

def get_steam_trending():
    try:
        s = requests.get("https://steamcharts.com/", headers=headers)
        s.raise_for_status()
        soup = BeautifulSoup(s.text, "html.parser")
        trending_table = soup.select("table.common-table")
        if trending_table:
            trending_rows = trending_table[0].select("tbody tr")[:5]
            return [
                f"🚀 {r.select('td')[0].text.strip()} – {r.select('td')[1].text.strip()} – 👥 {r.select('td')[3].text.strip()}"
                for r in trending_rows
            ]
        else:
            return ["Trending verisi bulunamadı veya tablo yapısı değişti."]
    except Exception as e:
        # print(f"Steam Trending verisi alınırken hata: {e}")
        return ["Steam Trending verisi alınamadı."]

def get_steam_records():
    try:
        s = requests.get("https://steamcharts.com/", headers=headers)
        s.raise_for_status()
        soup = BeautifulSoup(s.text, "html.parser")
        records_table = soup.select("table.common-table")
        if len(records_table) > 2:
            records_rows = records_table[2].select("tbody tr")[:5]
            return [
                f"🏅 {r.select('td')[0].text.strip()} – 👤 {r.select('td')[1].text.strip()} ({r.select('td')[2].text.strip()})"
                for r in records_rows
            ]
        else:
             return ["Steam Rekor verisi bulunamadı veya tablo yapısı değişti."]
    except Exception as e:
        # print(f"Steam Records verisi alınırken hata: {e}")
        return ["Steam Rekor verisi alınamadı."]

def get_steam_top():
    try:
        top_page = requests.get("https://steamcharts.com/top", headers=headers)
        top_page.raise_for_status()
        soup = BeautifulSoup(top_page.text, "html.parser")
        top_table = soup.select("table.common-table")
        if top_table:
             top_rows = top_table[0].select("tbody tr")[:5]
             return [
                f"🎮 {r.select('td')[1].text.strip()} – 👥 {r.select('td')[2].text.strip()} – ⏫ {r.select('td')[4].text.strip()}"
                for r in top_rows
            ]
        else:
            return ["En Popüler Oyunlar verisi bulunamadı veya tablo yapısı değişti."]
    except Exception as e:
        # print(f"Steam Top verisi alınırken hata: {e}")
        return ["En Popüler Oyunlar verisi alınamadı."]

def get_bundle_news():
    try:
        b = requests.get("https://www.bundle.app/gundem", headers=headers)
        b.raise_for_status()
        soup = BeautifulSoup(b.content, "html.parser")
        news_headlines = soup.find_all("h3")[:10]
        return [f"📰 {h.get_text(strip=True)}" for h in news_headlines]
    except Exception as e:
        # print(f"Bundle Gündem verisi alınırken hata: {e}")
        return ["Gündem verisi alınamadı."]


# === Deprem Verisi ===
def get_quakes():
    try:
        response = requests.get("http://www.koeri.boun.edu.tr/scripts/lst9.asp", headers=headers)
        response.raise_for_status()
        response.encoding = 'iso-8859-9'
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        pre_tag = soup.find("pre")
        if not pre_tag:
             return [{"time": "", "yer": "Deprem verisi formatı değişti", "mag": "?"}]

        lines = pre_tag.text.strip().split("\n")
        data_lines = lines[6:21]

        quakes = []
        for line in data_lines:
            p = line.split()
            if len(p) > 7:
                location_parts = p[7:]
                filtered_parts = [
                    part for part in location_parts
                    if part.strip() != '' and part.strip().lower() != 'ilksel'
                ]
                yer = " ".join(filtered_parts).strip()

                if not yer:
                    yer = "Deniz veya Belirtilmemiş Yer"

                time_str = f"{p[0]} {p[1]}"
                mag = p[6]

                quakes.append({
                    "time": time_str,
                    "yer": yer,
                    "mag": mag
                })
        return quakes
    except Exception as e:
        # st.error(f"Deprem verisi alınırken hata oluştu: {e}")
        return [{"time": "", "yer": "Deprem verisi alınamadı", "mag": "?"}]

# === Sesli Uyarı ===
def play_sound():
    st.markdown("""
        <audio autoplay="true">
        <source src="data:audio/wav;base64,UklGRigBAABXQVZFZm10IBAAAAABAAEARAEAASAAGwEABAAIAADazwAAZjwAAICAgIDeDxYCSUTjfAAAACAA==" type="audio/wav">
        </audio>
    """, unsafe_allow_html=True)

# === Canlı Saat JavaScript Kodu ===
live_clock_script = """
    <script>
    function updateLiveClock() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const timeString = `${hours}:${minutes}:${seconds}`;
        const clockElement = document.getElementById('live-clock');
        if (clockElement) {
            clockElement.innerText = timeString;
        }
    }
    updateLiveClock();
    setInterval(updateLiveClock, 1000);
    </script>
"""

# === Verileri Al (Bu kısım st_autorefresh ile periyodik çalışır) ===
trending_list = get_steam_trending()
record_list = get_steam_records()
top_list = get_steam_top()
news_list = get_bundle_news()
quakes = get_quakes()

# Deprem verisi değiştiyse ses çıkar
latest_quake_hash = [f"{q['time']} {q['yer']} {q['mag']}" for q in quakes]

if latest_quake_hash != st.session_state.last_quake_list:
     if st.session_state.last_quake_list:
        play_sound()
     st.session_state.last_quake_list = latest_quake_hash


# === GÖSTERİM (Alt Paneller) ===
col1, col2 = st.columns(2) # Ana içerik için 2 sütun

with col1:
    # Steam panelleri
    st.markdown('<div class="panel"><h3>📈 Steam Trending</h3><div class="scrollable-panel-content">' + "".join([f"<div class='item'>{i}</div>" for i in trending_list]) + "</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel"><h3>🎮 En Popüler Oyunlar</h3><div class="scrollable-panel-content">' + "".join([f"<div class='item'>{i}</div>" for i in top_list]) + "</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel"><h3>🏅 Oyuncu Rekorları</h3><div class="scrollable-panel-content">' + "".join([f"<div class='item'>{i}</div>" for i in record_list]) + "</div></div>", unsafe_allow_html=True)

with col2:
    # Sağ sütun içeriği
    st.markdown('<div class="panel"><h3>📰 Bundle Gündem</h3><div class="scrollable-panel-content">' + "".join([f"<div class='item'>{i}</div>" for i in news_list]) + "</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel"><h3>🌍 Son 15 Deprem (Kandilli)</h3><div class="scrollable-panel-content">' + "".join([f"<div class='item'>🗓 {q['time']} – 📍 {q['yer']} – <span class=\'highlight\'>{q['mag']}</span></div>" for q in quakes]) + "</div></div>", unsafe_allow_html=True)

Add full app.py dashboard code

