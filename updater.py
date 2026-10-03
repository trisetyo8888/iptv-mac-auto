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
    
    mac_clean = mac.replace(':', '').lower()
    device_id = hashlib.md5(mac_clean.encode()).hexdigest().upper()
    device_id2 = hashlib.md5(device_id.encode()).hexdigest().upper()
    
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
    
    # 1. Handshake
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
        print(f"[+] Handshake HTTP Status: {res_handshake.status_code}")
        print(f"[DEBUG] Handshake Raw Response: {res_handshake.text[:300]}")
        
        token = ""
        try:
            handshake_data = res_handshake.json()
            token = handshake_data.get('js', {}).get('token', '')
        except Exception:
            pass

        if token:
            cookies['Bearer'] = token
            session.cookies.update(cookies)
            print(f"[+] Token Sesi Ditemukan: {token}")
        else:
            session.cookies.update(cookies)
            print("[!] Token tidak ditemukan di JSON. Menggunakan otentikasi berbasis Cookie.")

        # 2. Get Profile
        profile_url = f"{portal_url}/portal.php?type=stb&action=get_profile&hd=1&ver=ImageDescription:%200.2.18-r14-pub-250&sn=123456789012&stb_type=MAG250&image_version=218&device_id={device_id}&js=true"
        if token:
            profile_url += f"&token={token}"
        res_prof = session.get(profile_url, cookies=session.cookies, timeout=15)
        print(f"[DEBUG] Profile Raw Response: {res_prof.text[:300]}")

        # 3. Get Channels (Mencoba request tanpa membatasi parameter token)
        ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels&force_ch_link_check=0&js=true"
        if token:
            ch_url += f"&token={token}"

        res_ch = session.get(ch_url, cookies=session.cookies, timeout=25)
        print(f"[+] Get Channels HTTP Status: {res_ch.status_code}")
        
        # CETAK RESPONS ASLI UNTUK ANALISIS JIKA GAGAL
        print(f"[DEBUG] Channels Raw Response (Teks asli dari Server):\n{res_ch.text[:1000]}")
        
        try:
            data = res_ch.json()
        except json.JSONDecodeError:
            print("[-] Gagal mengubah balasan server menjadi JSON. Server mungkin mengirimkan halaman proteksi HTML.")
            return

        channels = []
        if isinstance(data, dict):
            if 'js' in data:
                if isinstance(data['js'], dict) and 'results' in data['js']:
                    channels = data['js']['results']
                elif isinstance(data['js'], list):
                    channels = data['js']
            elif 'results' in data:
                channels = data['results']
        elif isinstance(data, list):
            channels = data

        if not channels:
            raise ValueError("Kanal kosong. Silakan periksa bagian [DEBUG] di atas untuk melihat penolakan server.")

        print(f"[+] Sukses mengekstrak {len(channels)} channel.")

        with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
            m3u.write("#EXTM3U\n")
            for ch in channels:
                if not isinstance(ch, dict):
                    continue
                name = ch.get('name', 'Unknown')
                cmd = ch.get('cmd', '')
                if cmd.startswith('ffmpeg '):
                    stream_url = cmd.replace('ffmpeg ', '')
                elif ' ' in cmd:
                    stream_url = cmd.split(' ')[-1]
                else:
                    stream_url = cmd
                    
                group = ch.get('tvg_id', 'TV')
                m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n')
                m3u.write(f'{stream_url}\n')
                
        print("[+] playlist.m3u berhasil diperbarui!")

    except Exception as e:
        print(f"[-] Terjadi kesalahan: {e}")
        raise e

if __name__ == "__main__":
    fetch_mac_portal()
