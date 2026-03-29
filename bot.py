import requests
import os
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Sreality API - hledáme byty 1+kk, 1+1, 2+kk, 2+1 v Ústí nad Labem
URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=2|3|4|5|6|7&category_type_cb=1&locality_district_id=88&locality_region_id=10&price_czk_max=3300000&per_page=50"

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def check_sreality(seen_ids):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(URL, headers=headers, timeout=15).json()
        for est in res.get('_embedded', {}).get('estates', []):
            est_id = str(est['hash_id'])
            loc = est.get('locality', '').lower()
            name = est.get('name', '').lower()
            
            # FILTR 1: Musí to být Klíše (vyhodí zbytek Ústí)
            if "klíše" not in loc:
                continue
            
            # FILTR 2: Stopka pro velké byty a domy (Sreality to občas podstrčí)
            stop_slova = ["3+", "4+", "5+", "atyp", "domu", "vily", "chata", "chalupa"]
            if any(s in name for s in stop_slova):
                continue

            if est_id not in seen_ids:
                price = est['price_czk']['value_raw']
                title = est['name']
                # OPRAVENÝ ODKAZ: Tento formát Sreality sežerou vždy
                link = f"https://www.sreality.cz/detail/prodej/byt/2+kk/usti-nad-labem-klise-klisska/{est_id}"
                
                msg = f"<b>🏠 NOVINKA KLÍŠE:</b>\n{title}\n💰 Cena: {price:,} Kč\n\n🔗 <a href='{link}'>Zobrazit inzerát</a>".replace(',', ' ')
                send_tg(msg)
                seen_ids.add(est_id)
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    file = "seen_ids.txt"
    seen = set(open(file).read().splitlines()) if os.path.exists(file) else set()
    check_sreality(seen)
    with open(file, "w") as f:
        f.write("\n".join(list(seen)[-100:]))
