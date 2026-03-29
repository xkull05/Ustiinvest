import requests
import os

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Sreality API - Hledáme byty v Ústí nad Labem (ID 88)
URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_district_id=88&locality_region_id=10&price_czk_max=3300000&per_page=60"

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def check_sreality():
    seen_file = "seen_ids.txt"
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            seen_ids = set(f.read().splitlines())
    else:
        seen_ids = set()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=15).json()
        new_ids = []

        for est in res.get('_embedded', {}).get('estates', []):
            est_id = str(est['hash_id'])
            name = est.get('name', '').lower()
            loc = est.get('locality', '').lower()
            
            # --- ŽELEZNÝ FILTR ---
            # Musí to být Klíše
            if "klíš" not in loc and "klis" not in loc:
                continue
            
            # Musí to být 1+ nebo 2+ (vyřadí 3+, 4+, 5+ a domy)
            if not any(size in name for size in ["1+kk", "1+1", "2+kk", "2+1"]):
                continue
            
            # Nesmí to být 3+kk (Sreality to občas míchají)
            if "3+" in name or "4+" in name or "5+" in name:
                continue
            # ---------------------

            if est_id not in seen_ids:
                price = est['price_czk']['value_raw']
                title = est['name']
                # UNIVERZÁLNÍ ODKAZ: Tohle Sreality vždycky spolkne a přesměruje
                link = f"https://www.sreality.cz/detail/prodej/byt/x/x/{est_id}"
                
                msg = f"<b>🏠 FILTROVÁNO: KLÍŠE (1-2kk)</b>\n{title}\n💰 Cena: {price:,} Kč\n\n🔗 <a href='{link}'>KLIKNI PRO DETAIL</a>".replace(',', ' ')
                send_tg(msg)
                seen_ids.add(est_id)
            
            new_ids.append(est_id)

        # Uložíme IDs
        with open(seen_file, "w") as f:
            f.write("\n".join(list(seen_ids)[-100:]))

    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    check_sreality()
