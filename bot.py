import requests
import os

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Sreality API - Ústí nad Labem (District 88)
URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_district_id=88&locality_region_id=10&per_page=60"

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def check_sreality():
    seen_file = "seen_ids.txt"
    seen_ids = set()
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            seen_ids = f.read().splitlines()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=15).json()
        estates = res.get('_embedded', {}).get('estates', [])
        
        valid_ids = []
        for est in estates:
            name = str(est.get('name', '')).lower()
            loc = str(est.get('locality', '')).lower()
            price = int(est.get('price_czk', {}).get('value_raw', 0))
            est_id = str(est['hash_id'])

            # --- AGRESIVNÍ FILTR (POKUD NESPLNÍ, OKAMŽITĚ KONČÍ) ---
            
            # 1. Musí to být Klíše (pokud není, jdeme na další)
            if "klíš" not in loc and "klis" not in loc:
                continue
                
            # 2. Cena musí být mezi 500 tis. a 3,3 mil. (vyřadí chyby a drahé vily)
            if price < 500000 or price > 3300000:
                continue
                
            # 3. Musí to být malý byt (vyřadí 3+, 4+, 5+ a domy)
            if any(bad in name for bad in ["3+", "4+", "5+", "atyp", "domu", "vily", "pozemek"]):
                continue
            
            # --- POKUD JSME DOŠLI SEM, JE TO TEN PRAVÝ BYT ---
            if est_id not in seen_ids:
                # UNIVERZÁLNÍ ODKAZ (ID na konci je klíčové)
                link = f"https://www.sreality.cz/detail/prodej/byt/2+kk/usti-nad-labem-klise-klisska/{est_id}"
                
                msg = f"<b>🎯 ZÁSAH! BYT NA KLÍŠI</b>\n{est.get('name')}\n💰 Cena: {price:,} Kč\n\n🔗 <a href='{link}'>ZOBRAZIT DETAIL</a>".replace(',', ' ')
                send_tg(msg)
                seen_ids.append(est_id)
            
            valid_ids.append(est_id)

        # Uložíme historii (posledních 50 ID)
        with open(seen_file, "w") as f:
            f.write("\n".join(seen_ids[-50:]))

    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    check_sreality()
