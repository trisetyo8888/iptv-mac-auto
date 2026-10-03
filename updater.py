      import os
import requests
import json

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
    
    # Base headers meniru perangkat MAG
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
        'Accept': '*/*',
        'Accept-Language': 'en-US,*',
        'X-User-Agent': 'model=MAG250;gAppVersion=2.18.04;rAppVersion=2.18.04;imageVersion=218;type=stb;sn=0000000000000',
    }

    session = requests.Session()
    session.headers.update(headers)
    
    # 1. Langkah Handshake & Ambil Token
    handshake_url = f"{portal_url}/portal.php?type=stb&action=handshake&js=true"
    cookies = {'mac': mac, 'stb_lang': 'en', 'timezone': 'GMT'}
    
    try:
        res_handshake = session.get(handshake_url, cookies=cookies, timeout=15)
        print(f"[+] Handshake Status Code: {res_handshake.status_code}")
        
        token = ""
        try:
            handshake_data = res_handshake.json()
            token = handshake_data.get('js', {}).get('token', '')
        except Exception:
            # Jika respons bukan JSON murni, coba bersihkan
            pass

        # Gabungkan token ke dalam cookies untuk request selanjutnya
        if token:
            cookies['Bearer'] = token
            session.cookies.update(cookies)
            print(f"[+] Berhasil mendapatkan Token Sesi.")
        else:
            # Beberapa portal menyisipkan token langsung lewat Cookies internal
            session.cookies.update(cookies)
            print("[!] Token eksplisit tidak ditemukan di JSON, mencoba menggunakan Cookie dasar...")

        # 2. Ambil Daftar Channel (Ditambahkan parameter token & opsi tambahan)
        ch_url = f"{portal_url}/portal.php?type=itv&action=get_all_channels&force_ch_link_check=0&js=true"
        if token:
            ch_url += f"&token={token}"

        res_ch = session.get(ch_url, cookies=session.cookies, timeout=20)
        print(f"[+] Get Channels Status Code: {res_ch.status_code}")
        
        try:
            data = res_ch.json()
        except json.JSONDecodeError:
            print("[-] Gagal mendecode respons portal sebagai JSON.")
            return

        # Ekstraksi data channel dari struktur Stalker
        channels = []
        if isinstance(data, dict):
            if 'js' in data and isinstance(data['js'], dict) and 'results' in data['js']:
                channels = data['js']['results']
            elif 'js' in data and isinstance(data['js'], list):
                channels = data['js']
            elif 'results' in data:
                channels = data['results']

        if not channels:
            raise ValueError("Portal mengembalikan data kosong. Kemungkinan MAC diblokir, kedaluwarsa, atau butuh API signature khusus.")

        print(f"[+] Berhasil menemukan {len(channels)} saluran TV.")

        # 3. Tulis ke file playlist.m3u
        with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
            m3u.write("#EXTM3U\n")
            for ch in channels:
                if not isinstance(ch, dict):
                    continue
                name = ch.get('name', 'Unknown Channel')
                cmd = ch.get('cmd', '')
                
                # Bersihkan prefix portal internal jika ada (contoh: ffmpeg http://...)
                if cmd.startswith('ffmpeg '):
                    stream_url = cmd.replace('ffmpeg ', '')
                elif ' ' in cmd:
                    stream_url = cmd.split(' ')[-1]
                else:
                    stream_url = cmd
                    
                # Format tag M3U standar
                group = ch.get('tvg_id', 'General')
                m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n')
                m3u.write(f'{stream_url}\n')
                
        print("[+] Berhasil memperbarui playlist.m3u")

    except Exception as e:
        print(f"[-] Terjadi Eror: {e}")
        # Memicu GitHub Actions agar statusnya bertanda silang merah jika gagal
        raise e

if __name__ == "__main__":
    fetch_mac_portal()              
