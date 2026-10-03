import os
import requests
import json
import hashlib

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        print("[-] File portal.txt tidak ditemukan!")
        return
        
    with open('portal.txt', 'r') as f:
        line = f.readline().strip()
        if not line or '|' not in line:
            print("[-] Format portal.txt salah. Gunakan: URL|MAC")
            return
        portal_url, mac = line.split('|')

    portal_url = portal_url.rstrip('/')
    print(f"[*] Menghubungi Portal: {portal_url}")
    print(f"[*] Menggunakan MAC: {mac}")
    
    # Membuat Device ID tiruan berbasis MAC untuk validasi keamanan ekstra
    mac_clean = mac.replace(':', '').lower()
    device_id = hashlib.md5(mac_clean.encode()).hexdigest().upper()
    device_id2 = hashlib.md5(device_id.encode()).hexdigest().upper()
    
    # Headers lengkap meniru persis aplikasi STB resmi / MAG Box
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
        'X-User-Agent': 'model=MAG250;gAppVersion=2.18.04;rAppVersion=2.18.04;imageVersion=218;type=stb;sn=123456789012;device_id=' + device_id,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'{portal_url}/c/',
        'Connection': 'keep-alive'
    }

    session = requests.Session()
    session.headers.update(headers)
    
    # 1. Langkah Handshake & Pembuatan Sesi
    handshake_url = f"{portal_url}/portal.php?type=stb&action=handshake&js=true"
    cookies = {
        'mac': mac, 
        'stb_lang': 'en', 
        'timezone': 'Europe/London',
        'device_id': device_id,
        'device_id2': device_id2
    }
    
    try:
        res_handshake = session.get(handshake_url, cookies=cookies, timeout=15)
        print(f"[+] Handshake Status Code: {res_handshake.status_code}")
        
        token = ""
        try:
            handshake_data = res_handshake.json()
            token = handshake_data.get('js', {}).get('token', '')
        except Exception:
            pass

        if token:
            cookies['Bearer'] = token
            session.cookies.update(cookies)
            print(f"[+] Berhasil mendapatkan Token Sesi.")
        else:
            session.cookies.update(cookies)
            print("[!] Token eksplisit tidak ditemukan di respons JSON. Mencoba dengan otentikasi Cookie...")

        # 2. Langkah Pemanggilan Profil Perangkat (Wajib bagi beberapa portal sebelum meminta data channel)
        profile_url = f"{portal_url}/portal.php?type=stb&action=get_profile&hd=1&ver=ImageDescription:%200.2.18-r14-pub-250;%20ImageDate:%20Fri%20Jan%2015%2017:33:04%20EET%202016;%20PORTAL%20version:%205.0.1;%20API%20Version:%20JS%20API%20version:%20328;%20STB%20version:%20Mini;%20Webkit%20version:%20533.3&sn=123456789012&stb_type=MAG250&image_version=218&video_out=hdmi&device_id={device_id}&device_id2={device_id2}&js=true"
        if token:
            profile_url += f"&token={token}"
        session.get(profile_url, cookies=session.cookies, timeout=15)

        # 3. Langkah Pengambilan Semua Saluran TV
        ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels&force_ch_link_check=0&js=true"
        if token:
            ch_url += f"&token={token}"

        res_ch = session.get(ch_url, cookies=session.cookies, timeout=25)
        print(f"[+] Get Channels Status Code: {res_ch.status_code}")
        
        try:
            data = res_ch.json()
        except json.JSONDecodeError:
            print("[-] Gagal mendecode respons portal sebagai JSON.")
            return

        # Ekstraksi data channel
        channels = []
        if isinstance(data, dict):
            if 'js' in data and isinstance(data['js'], dict) and 'results' in data['js']:
                channels = data['js']['results']
            elif 'js' in data and isinstance(data['js'], list):
                channels = data['js']
            elif 'results' in data:
                channels = data['results']

        if not channels:
            raise ValueError("Portal mengembalikan data kosong. Sistem keamanan portal mendeteksi bot atau membutuhkan tanda tangan enkripsi tingkat tinggi.")

        print(f"[+] Sukses! Berhasil mengamankan {len(channels)} saluran TV.")

        # 4. Tulis file output playlist.m3u
        with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
            m3u.write("#EXTM3U\n")
            for ch in channels:
                if not isinstance(ch, dict):
                    continue
                name = ch.get('name', 'Unknown Channel')
                cmd = ch.get('cmd', '')
                
                # Membersihkan sintaks player internal bawaan portal
                if cmd.startswith('ffmpeg '):
                    stream_url = cmd.replace('ffmpeg ', '')
                elif ' ' in cmd:
                    stream_url = cmd.split(' ')[-1]
                else:
                    stream_url = cmd
                    
                group = ch.get('tvg_id', 'General')
                m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n')
                m3u.write(f'{stream_url}\n')
                
        print("[+] Berhasil memperbarui playlist.m3u secara otomatis.")

    except Exception as e:
        print(f"[-] Terjadi Eror: {e}")
        raise e

if __name__ == "__main__":
    fetch_mac_portal()

      
