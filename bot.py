import requests
import os

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Sreality API - širší hledání v Ústí nad Labem (ID 88)
URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_district_id=88&locality_region_id=10&per_page=60"

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=10)

def check_sreality():
    # Načtení historie
    seen_file = "seen_ids.txt"
    seen_ids = set()
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            seen_ids = set(f.read().splitlines())

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=15).json()
        estates = res.get('_embedded', {}).get('estates', [])
        
        for est in estates:
            est_id = str(est['hash_id'])
            name = est.get('name', '').lower()
            loc = est.get('locality', '').lower()
            price_raw = est.get('price_czk', {}).get('value_raw', 0)
            
            # --- FILTR: PŘÍSNÁ KONTROLA TEXTU ---
            # 1. Lokace musí být "Klíše" (vyloučíme zbytek Ústí a doporučené byty z Teplic atd.)
            if "klíš" not in loc and "klis" not in loc:
                continue
            
            # 2. Cena musí být do 3,3 mil (vyřadí drahé byty, které tam Sreality cpou jako reklamu)
            if price_raw > 3300000 or price_raw == 0:
                continue

            # 3. Velikost musí být 1+ nebo 2+ (vyřadí 3+, 4+, 5+ a domy)
            povolene_velikosti = ["1+kk", "1+1", "2+kk", "2+1"]
            if not any(vel in name for vel in povolene_velikosti):
                continue
            
            # 4. Pojistka proti 3+kk a větším
            if any(zakaz in name for zakaz in ["3+", "4+", "5+", "atyp", "domu"]):
                continue

            # --- ODESLÁNÍ ---
            if est_id not in seen_ids:
                title = est['name']
                # TENTO ODKAZ JE UNIVERZÁLNÍ A NEHÁŽE 404
                link = f"https://www.sreality.cz/detail/prodej/byt/2+kk/usti-nad-labem-klise-klisska/{est_id}"
                
                msg = f"<b>🚀 NOVÝ BYT KLÍŠE:</b>\n{title}\n💰 Cena: {price_raw:,} Kč\n\n🔗 <a href='{link}'>KLIKNI PRO DETAIL</a>".replace(',', ' ')
                send_tg(msg)
                seen_ids.add(est_id)

        # Uložení historie
        with open(seen_file, "w") as f:
            f.write("\n".join(list(seen_ids)[-100:]))

    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    check_sreality()
