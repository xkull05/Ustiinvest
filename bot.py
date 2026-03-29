import requests
import os

# Načtení klíčů z GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Sreality API - Ústí nad Labem
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
            seen_ids = set(f.read().splitlines())

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=15).json()
        estates = res.get('_embedded', {}).get('estates', [])
        
        found_something = False
        for est in estates:
            name = est.get('name', '').lower()
            loc = est.get('locality', '').lower()
            price = est.get('price_czk', {}).get('value_raw', 0)
            est_id = str(est['hash_id'])

            # --- TOTÁLNÍ FILTR (POUZE KLÍŠE A MALÉ BYTY) ---
            if "klíš" not in loc and "klis" not in loc:
                continue
            if price > 3500000 or price == 0:
                continue
            if any(bad in name for bad in ["3+", "4+", "5+", "atyp", "domu", "vily"]):
                continue
            # -----------------------------------------------

            if est_id not in seen_ids:
                found_something = True
                link = f"https://www.sreality.cz/detail/prodej/byt/2+kk/usti-nad-labem-klise-klisska/{est_id}"
                msg = f"<b>🏠 KLÍŠE - ÚSTÍ:</b>\n{est.get('name')}\n💰 Cena: {price:,} Kč\n\n🔗 <a href='{link}'>OTEVŘÍT INZERÁT</a>".replace(',', ' ')
                send_tg(msg)
                seen_ids.add(est_id)

        # Pokud bot nic nového nenašel, pošle ti aspoň jednou "Test OK" (můžeš pak smazat)
        # send_tg("<i>Bot zkontroloval Klíši - nic nového.</i>") 

        with open(seen_file, "w") as f:
            f.write("\n".join(list(seen_ids)[-100:]))

    except Exception as e:
        send_tg(f"Chyba bota: {e}")

if __name__ == "__main__":
    check_sreality()
