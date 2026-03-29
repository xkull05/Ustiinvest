import requests
import os

# Načtení klíčů z trezoru GitHubu
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
# URL pro 1+kk a 2+kk na Klíši do 3.2M
URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_district_id=88&locality_region_id=10&price_czk_max=3200000&per_page=20"

def check_sreality():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(URL, headers=headers).json()
        
        # Načtení už viděných ID
        try:
            with open("seen_ids.txt", "r") as f:
                seen_ids = f.read().splitlines()
        except FileNotFoundError:
            seen_ids = []

        new_ids = []
        for estate in response.get('_embedded', {}).get('estates', []):
            est_id = str(estate['hash_id'])
            new_ids.append(est_id)
            
            if est_id not in seen_ids:
                name = estate['name']
                price = estate['price_czk']['value_raw']
                link = f"https://www.sreality.cz/detail/prodej/byt/x/x/{est_id}"
                msg = f"🏠 NOVÁ ŠANCE NA KLÍŠI!\n{name}\nCena: {price} Kč\n{link}"
                
                # Odeslání na Telegram
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                              data={"chat_id": CHAT_ID, "text": msg})

        # Uložení aktuálních ID pro příště
        with open("seen_ids.txt", "w") as f:
            f.write("\n".join(new_ids))
            
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    check_sreality()
