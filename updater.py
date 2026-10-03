import os
import requests
import json
import hashlib
import re

def get_country_group(channel_name):
    name = channel_name.strip()
    
    # 1. Regex untuk mendeteksi pola pembungkus di awal nama (contoh: |FR|, [NL], ┃UCL┃, (US))
    # Pola ini mengambil teks di dalam simbol pembungkus tanpa menyertakan simbolnya
    match_brackets = re.match(r'^[\s\-_]*[\[┃\|\(]([A-Za-z0-9\s\+\-\&\.]+)[\]┃\|\)]', name)
    if match_brackets:
        detected_group = match_brackets.group(1).strip()
        # Batasi panjang karakter agar tidak salah mengambil potongan kalimat panjang
        if 2 <= len(detected_group) <= 15:
            return detected_group.upper()

    # 2. Regex cadangan untuk mendeteksi pola tanda titik dua di awal nama (contoh: US: HBO, ID: TRANS7)
    match_colon = re.match(r'^[\s\-_]*([A-Za-z0-9]{2,4})[\s\-_]*:', name)
    if match_colon:
        detected_group = match_colon.group(1).strip()
        return detected_group.upper()

    # 3. Regex cadangan untuk kata kunci mandiri di awal nama tanpa simbol (contoh: UFC 290, Boxing Live)
    match_word = re.match(r'^[\s\-_]*(UFC|LIVE EVENT|BOXING|LIVE FOOTBALL|TENNIS|MLB|MLS|WNBA|NCAA|RT)[\s\-_]*', name, re.IGNORECASE)
    if match_word:
        return match_word.group(1).strip().upper()

    # Jika nama channel tidak memiliki pola awalan kategori sama sekali
    return "OTHERS"

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        print("[-] File portal.txt tidak ditemukan!")
        return
        
    with open('portal.txt', 'r') as f:
        lines = f.readlines()

    portal_sukses = 0

    # Memproses file playlist secara terpisah: playlist_1.m3u, playlist_2.m3u, playlist_3.m3u
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
                    
                    # Sortir murni berdasarkan pola awalan tvg-name (nama channel)
                    final_group = get_country_group(name)
                    
                    m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{final_group}",{name}\n')
                    m3u.write(f'{stream_url}\n')
                    
            print(f"[+] File {filename} sukses disimpan!")
            portal_sukses += 1

        except Exception as e:
            print(f"[-] Eror pada portal baris {index}: {e}")
            continue

    print(f"\n[+] SELESAI! {portal_sukses} file playlist siap digunakan.")

if __name__ == "__main__":
    fetch_mac_portal()
