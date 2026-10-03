import os
import requests
import json
import hashlib
import re

def get_country_group(channel_name, original_group):
    name = channel_name.strip()
    
    # 1. KAMUS DATA UTAMA (Dictionary yang benar menggunakan pasangan 'KATA': 'NAMA GRUP')
    # Seluruh kata kunci ditulis dalam huruf besar (UPPERCASE) tanpa tanda baca pembungkus
    country_map = {
        # Kode Liga / Event Khusus
        'UCL': '┃UCL┃',
        'NLZIET': '┃NLZIET┃',
        'CANAL+': '┃CANAL+┃',
        'UFC': 'UFC',
        'LIVE EVENT': 'LIVE EVENT',
        'BOXING': 'BOXING',
        'LIVE FOOTBALL': 'LIVE FOOTBALL',
        'MOTOGP': '| MOTOGP |',
        'MXGP': '| MXGP |',
        'F1 TV': '| F1 TV |',
        'TENNIS': 'TENNIS',
        'MLB': 'MLB',
        'MILB': '| MiLB |',
        'MLS': '| MLS |',
        'WNBA': '| WNBA |',
        'NCAAW': '| NCAAW |',
        'NJCAA': '| NJCAA |',
        'NCAA': '| NCAA |',
        'DISNEY FR': 'DISNEY FRANCE',
        
        # Pemetaan Kode Huruf Negara Utama ke Nama Folder Rapi
        'NL': 'NETHERLANDS',
        'FR': 'FRANCE',
        'EN': 'ENGLISH',
        'BE': 'BELGIUM',
        'VTM GO+': 'BELGIUM VTM GO',
        'LU': 'LUXEMBOURG',
        'DE': 'GERMANY',
        'UK': 'UNITED KINGDOM',
        'IE': 'IRELAND',
        'CH': 'SWITZERLAND',
        'AT': 'AUSTRIA',
        'AL': 'ALBANIA',
        'GR': 'GREECE',
        'CY': 'CYPRUS',
        'IT': 'ITALY',
        'ES': 'SPAIN',
        'USA': 'UNITED STATES',
        'US': 'UNITED STATES',
        'CA FR': 'CANADA FRENCH',
        'CA EN': 'CANADA ENGLISH',
        'NZ': 'NEW ZEALAND',
        'TR': 'TURKEY',
        'RS': 'SERBIA',
        'BA': 'BOSNIA',
        'HR': 'CROATIA',
        'MK': 'MACEDONIA',
        'ME': 'MONTENEGRO',
        'SI': 'SLOVENIA',
        'EXYU': 'EX-YUGOSLAVIA',
        'BG': 'BULGARIA',
        'RO': 'ROMANIA',
        'CZ': 'CZECH REPUBLIC',
        'HU': 'HUNGARY',
        'PL': 'POLAND',
        'PT': 'PORTUGAL',
        'AR': 'ARABIC',
        'MA': 'MOROCCO',
        'DZ': 'ALGERIA',
        'TN': 'TUNISIA',
        'OSN': 'OSN NETWORK',
        'EG': 'EGYPT',
        'AE': 'UAE',
        'IQ': 'IRAQ',
        'SA': 'SAUDI ARABIA',
        'PS': 'PALESTINE',
        'JO': 'JORDAN',
        'LY': 'LIBYA',
        'SU': 'SUDAN',
        'YE': 'YEMEN',
        'QAT': 'QATAR',
        'KU': 'KUWAIT',
        'KURD': 'KURDISTAN',
        'KURD - SAT': 'KURDISTAN',
        'KURD - DVB T': 'KURDISTAN',
        'AFG': 'AFGHANISTAN',
        'AF': 'AFGHANISTAN',
        'IR': 'IRAN',
        'SOM': 'SOMALIA',
        'SN': 'SENEGAL',
        'GH': 'GHANA',
        'NG': 'NIGERIA',
        'KE': 'KENYA',
        'DRC': 'CONGO',
        'CM': 'CAMEROON',
        'ET': 'ETHIOPIA',
        'TG': 'TOGO',
        'GN': 'GUINEA',
        'GA': 'GABON',
        'CI': 'IVORY COAST',
        'AO': 'ANGOLA',
        'BF': 'BURKINA FASO',
        'BJ': 'BENIN',
        'TZ': 'TANZANIA',
        'UG': 'UGANDA',
        'MZ': 'MOZAMBIQUE',
        'RW': 'RWANDA',
        'RT': 'RUSSIA TODAY',
    }

    # 2. LOGIKA STRIP PINTAR (Mengekstrak kata kunci bersih di awal teks tanpa peduli simbol pembungkusnya)
    # Menghapus simbol seperti |, ┃, [, ], (, ), -, dan spasi di bagian depan nama channel
    clean_prefix = re.sub(r'^[┃\s\[\|\(\-_]*', '', name).upper()
    
    # Mencari apakah teks depan tersebut diawali oleh salah satu kata kunci di kamus kita
    for keyword, group_name in country_map.items():
        if clean_prefix.startswith(keyword):
            return group_name

    # 3. LOGIKA DETEKSI OTOMATIS BILA ADA KODE BARU (Auto-Fallback)
    # Jika ada kode awal terbungkus simbol (seperti |XYZ|) yang belum terdaftar di kamus atas,
    # skrip otomatis akan menjadikannya nama folder "XYZ" daripada membuangnya ke folder OTHERS.
    match_fallback = re.match(r'^[\s\-_]*[\[┃\|\(]([A-Za-z0-9\s\-]+)[\]┃\|\)]', name)
    if match_fallback:
        detected_code = match_fallback.group(1).strip().upper()
        if len(detected_code) <= 12: # Batasi agar bukan kalimat panjang yang terambil
            return detected_code

    # 4. Jika benar-benar polosan, gunakan nama grup bawaan dari server portal
    if original_group and str(original_group).strip() != "" and str(original_group).lower() != "general":
        return str(original_group)
        
    return "OTHERS"

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        print("[-] File portal.txt tidak ditemukan!")
        return
        
    with open('portal.txt', 'r') as f:
        lines = f.readlines()

    portal_sukses = 0

    # Memproses 3 file playlist secara terpisah: playlist_1.m3u, playlist_2.m3u, playlist_3.m3u
    for index, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or '|' not in line:
            continue
            
        filename = f"playlist_{index}.m3u"
        try:
            portal_url, mac = line.split('|')
            portal_url = portal_url.rstrip('/')
            
            print(f"\n[*] [{index}/{len(lines)}] Memproses: {portal_url}")
            print(f"[*] Menggunakan MAC: {mac} -> Output: {filename}")
            
            mac_clean = mac.replace(':', '').lower()
            device_id = hashlib.md5(mac_clean.encode()).hexdigest().upper()
            device_id2 = hashlib.md5(device_id.encode()).hexdigest().upper()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
                'X-User-Agent': f'model=MAG250;gAppVersion=2.18.04;rAppVersion=2.18.04;imageVersion=218;type=stb;sn=123456789012;device_id={device_id}',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': f'{portal_url}/c/',
                'Connection': 'keep-alive'
            }

            session = requests.Session()
            session.headers.update(headers)
            
            # Handshake
            handshake_url = f"{portal_url}/portal.php?type=stb&action=handshake&js=true"
            cookies = {'mac': mac, 'stb_lang': 'en', 'timezone': 'Europe/London', 'device_id': device_id, 'device_id2': device_id2}
            
            res_handshake = session.get(handshake_url, cookies=cookies, timeout=12)
            token = ""
            try:
                token = res_handshake.json().get('js', {}).get('token', '')
            except:
                pass

            if token:
                cookies['Bearer'] = token
                session.cookies.update(cookies)

            # Get Profile
            profile_url = f"{portal_url}/portal.php?type=stb&action=get_profile&hd=1&ver=ImageDescription:%200.2.18-r14-pub-250&sn=123456789012;device_id={device_id}&js=true"
            if token: profile_url += f"&token={token}"
            session.get(profile_url, cookies=session.cookies, timeout=12)

            # Get Channels
            ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels&force_ch_link_check=0&js=true"
            if token: ch_url += f"&token={token}"

            res_ch = session.get(ch_url, cookies=session.cookies, timeout=25)
            data = res_ch.json()

            channels = []
            if isinstance(data, dict):
                if 'js' in data and isinstance(data['js'], dict):
                    if 'data' in data['js'] and isinstance(data['js']['data'], list): channels = data['js']['data']
                    elif 'results' in data['js'] and isinstance(data['js']['results'], list): channels = data['js']['results']
                elif 'data' in data and isinstance(data['data'], list): channels = data['data']
                elif 'results' in data and isinstance(data['results'], list): channels = data['results']
            elif isinstance(data, list):
                channels = data

            if not channels:
                print(f"[!] Gagal mengambil channel untuk {portal_url}")
                continue

            print(f"[+] Berhasil memproses {len(channels)} saluran mentah.")

            # Tulis ke file playlist masing-masing
            with open(filename, 'w', encoding='utf-8') as m3u:
                m3u.write("#EXTM3U\n")
                for ch in channels:
                    if not isinstance(ch, dict): continue
                    name = ch.get('name', 'Unknown Channel')
                    cmd = ch.get('cmd', '')
                    if not cmd: continue
                        
                    if cmd.startswith('ffmpeg '): stream_url = cmd.replace('ffmpeg ', '')
                    elif ' ' in cmd: stream_url = cmd.split(' ')[-1]
                    else: stream_url = cmd
                    
                    # Ambil grup asli portal
                    portal_group = ch.get('tvg_id', ch.get('category_id', 'General'))
                    
                    # Sortir dinamis berdasarkan kata kunci awal nama channel
                    final_group = get_country_group(name, portal_group)
                    
                    m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{final_group}",{name}\n')
                    m3u.write(f'{stream_url}\n')
                    
            print(f"[+] File {filename} sukses disimpan dengan kategori teratur!")
            portal_sukses += 1

        except Exception as e:
            print(f"[-] Eror pada portal baris {index}: {e}")
            continue

    print(f"\n[+] SELESAI! {portal_sukses} file playlist siap digunakan.")

if __name__ == "__main__":
    fetch_mac_portal()
