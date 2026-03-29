import requests
import os
from bs4 import BeautifulSoup

# Načtení klíčů z trezoru GitHubu
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# Konfigurace - FILTRY
# Sreality: 1+kk, 2+kk, Ústí nad Labem (Klíše), do 3.2M
SREALITY_URL = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_district_id=88&locality_region_id=10&price_czk_max=3200000&per_page=40"

# Bazoš: Hledáme slovo "klise" v sekci Reality, lokalita Ústí (40001)
BAZOS_URL = "https://reality.bazos.cz/hledat/klise/?hledat=klise&rubriky=reality&hlokalita=40001&humkreis=0&cenaod=&cenado=3200000&order=1"

def send_tg(msg):
    """Odeslání zprávy na Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Chyba při odesílání na TG: {e}")

def check_sreality(seen_ids):
    """Kontrola Srealit s filtrem na Klíši"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(SREALITY_URL, headers=headers, timeout=15)
        data = response.json()
        
        for estate in data.get('_embedded', {}).get('estates', []):
            est_id = str(estate['hash_id'])
            locality = estate.get('locality', '').lower()
            name = estate.get('name', '').lower()
            
            # PŘÍSNÝ FILTR: Musí to být Ústí a musí tam být slovo Klíše
            if "ústí nad labem" in locality and "klíše" in locality:
                if est_id not in seen_ids:
                    price = estate['price_czk']['value_raw']
                    title = estate['name']
                    link = f"https://www.sreality.cz/detail/prodej/byt/x/x/{est_id}"
                    
                    msg = f"<b>🏠 SREALITY: KLÍŠE</b>\n{title}\n💰 Cena: {price:,} Kč\n\n🔗 <a href='{link}'>Otevřít inzerát</a>".replace(',', ' ')
                    send_tg(msg)
                    seen_ids.add(est_id)
    except Exception as e:
        print(f"Chyba Sreality: {e}")

def check_bazos(seen_ids):
    """Kontrola Bazoše"""
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'}
    try:
        response = requests.get(BAZOS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Bazoš inzeráty jsou v tabulkách/divu s třídou 'vypis'
        for div in soup.find_all('div', class_='vypis'):
            link_tag = div.find('a')
            if not link_tag: continue
            
            link = "https://reality.bazos.cz" + link_tag['href']
            # ID inzerátu získáme z konce URL
            est_id = "bazos_" + link.split('/')[-2]
            
            title = div.find('h2').text
            
            # Kontrola, zda je "klíše" v názvu (Bazoš občas hází i okolí)
            if "klíš" in title.lower() or "klis" in title.lower():
                if est_id not in seen_ids:
                    price = div.find('div', class_='cena').text
                    msg = f"<b>💰 BAZOŠ: NOVÝ INZERÁT</b>\n{title}\n💵 Cena: {price}\n\n🔗 <a href='{link}'>Otevřít Bazoš</a>"
                    send_tg(msg)
                    seen_ids.add(est_id)
    except Exception as e:
        print(f"Chyba Bazoš: {e}")

if __name__ == "__main__":
    # 1. Načtení historie viděných ID
    seen_file = "seen_ids.txt"
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            seen_ids = set(f.read().splitlines())
    else:
        seen_ids = set()

    # 2. Spuštění kontrol
    check_sreality(seen_ids)
    check_bazos(seen_ids)

    # 3. Uložení aktualizované historie (max posledních 100 ID, ať soubor neroste do nekonečna)
    with open(seen_file, "w") as f:
        f.write("\n".join(list(seen_ids)[-100:]))
