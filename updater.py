import os
import requests
import json
import hashlib

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        print("[-] File portal.txt tidak ditemukan!")
        return
        
    with open('portal.txt', 'r') as f:
        lines = f.readlines()

    # Buka/Buat file playlist baru dan bersihkan isinya di awal
    with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
        m3u.write("#EXTM3U\n")

    total_all_channels = 0

    # Lakukan perulangan untuk setiap baris portal di portal.txt
    for index, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or '|' not in line:
            continue
            
        portal_url, mac = line.split('|')
        portal_url = portal_url.rstrip('/')
        
        print(f"\n[*] [{index}/{len(lines)}] Memproses: {portal_url}")
        print(f"[*] Menggunakan MAC: {mac}")
        
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
        
        # 1. Handshake
        handshake_url = f"{portal_url}/portal.php?type=stb&action=handshake&js=true"
        cookies = {'mac': mac, 'stb_lang': 'en', 'timezone': 'Europe/London', 'device_id': device_id, 'device_id2': device_id2}
        
        try:
            res_handshake = session.get(handshake_url, cookies=cookies, timeout=15)
            token = ""
            try:
                token = res_handshake.json().get('js', {}).get('token', '')
            except:
                pass

            if token:
                cookies['Bearer'] = token
                session.cookies.update(cookies)

            # 2. Get Profile
            profile_url = f"{portal_url}/portal.php?type=stb&action=get_profile&hd=1&ver=ImageDescription:%200.2.18-r14-pub-250&sn=123456789012&stb_type=MAG250&image_version=218&device_id={device_id}&js=true"
            if token: profile_url += f"&token={token}"
            session.get(profile_url, cookies=session.cookies, timeout=15)

            # 3. Get Channels
            ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels&force_ch_link_check=0&js=true"
            if token: ch_url += f"&token={token}"

            res_ch = session.get(ch_url, cookies=session.cookies, timeout=30)
            data = res_ch.json()

            channels = []
            if isinstance(data, dict):
                if 'js' in data and isinstance(data['js'], dict) and 'data' in data['js']: channels = data['js']['data']
                elif 'js' in data and isinstance(data['js'], dict) and 'results' in data['js']: channels = data['js']['results']
                elif 'js' in data and isinstance(data['js'], list): channels = data['js']
                elif 'data' in data and isinstance(data['data'], list): channels = data['data']
                elif 'results' in data and isinstance(data['results'], list): channels = data['results']
            elif isinstance(data, list):
                channels = data

            if not channels:
                print(f"[!] Gagal mengambil channel dari portal ini (Kosong).")
                continue

            print(f"[+] Berhasil mengambil {len(channels)} channel.")
            total_all_channels += len(channels)

            # 4. Tulis (Append) ke playlist.m3u
            with open('playlist.m3u', 'a', encoding='utf-8') as m3u:
                for ch in channels:
                    if not isinstance(ch, dict): continue
                    name = ch.get('name', 'Unknown Channel')
                    cmd = ch.get('cmd', '')
                    if not cmd: continue
                        
                    if cmd.startswith('ffmpeg '): stream_url = cmd.replace('ffmpeg ', '')
                    elif ' ' in cmd: stream_url = cmd.split(' ')[-1]
                    else: stream_url = cmd
                        
                    # Memberikan nama grup unik berdasarkan urutan portal agar tidak tertukar
                    group = f"Portal {index} - " + str(ch.get('tvg_id', ch.get('category_id', 'General')))
                    m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n')
                    m3u.write(f'{stream_url}\n')

        except Exception as e:
            print(f"[-] Kendala pada portal ini: {e}")
            continue

    print(f"\n[+] SELESAI! Total keseluruhan: {total_all_channels} channel digabungkan ke playlist.m3u")

if __name__ == "__main__":
    fetch_mac_portal()
