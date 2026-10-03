import os
import requests

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        raise FileNotFoundError("File 'portal.txt' tidak ditemukan di repositori!")
        
    with open('portal.txt', 'r') as f:
        line = f.readline().strip()
        if not line or '|' not in line:
            raise ValueError("Format di portal.txt salah. Harus berupa: URL|MAC")
        portal_url, mac = line.split('|')

    portal_url = portal_url.rstrip('/')
    print(f"[*] Menghubungi Portal: {portal_url}")
    print(f"[*] Menggunakan MAC: {mac}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
        'Cookie': f'mac={mac}'
    }
    
    # 1. Langkah Handshake
    handshake_url = f"{portal_url}/portal.php?type=stb&action=handshake&js=true"
    try:
        req_handshake = requests.get(handshake_url, headers=headers, timeout=15)
        print(f"[+] Handshake Status Code: {req_handshake.status_code}")
    except Exception as e:
        raise ConnectionError(f"Gagal melakukan handshake ke portal: {e}")

    # 2. Langkah Mengambil Semua Channel
    ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels"
    try:
        res_ch = requests.get(ch_url, headers=headers, timeout=20)
        print(f"[+] Get Channels Status Code: {res_ch.status_code}")
        data = res_ch.json()
    except Exception as e:
        raise ConnectionError(f"Gagal mengambil data channel atau response bukan JSON: {e}")
        
    # 3. Validasi & Parsing Data JSON Portal
    channels = []
    if isinstance(data, dict):
        if 'js' in data and isinstance(data['js'], dict) and 'results' in data['js']:
            channels = data['js']['results']
        elif 'results' in data:
            channels = data['results']

    if not channels:
        print("[-] Respons JSON dari Portal:")
        print(data)
        raise ValueError("Gagal mendapatkan daftar channel. Portal mengembalikan data kosong atau MAC diblokir/expired.")

    # 4. Tulis ke file playlist.m3u
    print(f"[+] Berhasil menemukan {len(channels)} channel. Menulis ke playlist.m3u...")
    with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
        m3u.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get('name', 'Unknown Channel')
            cmd = ch.get('cmd', '')
            
            # Ekstrak link streaming m3u8 / ts dari perintah portal
            if not cmd:
                continue
            if ' ' in cmd:
                parts = cmd.split(' ')
                stream_url = parts[-1] if parts[-1].startswith('http') else cmd
            else:
                stream_url = cmd
                
            m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="MAC Portal",{name}\n')
            m3u.write(f'{stream_url}\n')
            
    print("[+] File playlist.m3u sukses dibuat!")

if __name__ == "__main__":
    fetch_mac_portal()
