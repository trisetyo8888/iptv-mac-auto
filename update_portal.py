import requests
import json
import re

def fetch_stalker_to_m3u():
    try:
        # 1. Membaca data URL dan MAC dari portal.txt
        with open("portal.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if len(lines) < 2:
            print("Error: portal.txt harus berisi URL di baris ke-1 dan MAC di baris ke-2.")
            return
            
        # PERBAIKAN: Mengambil baris indeks secara tepat
        raw_url = lines[0]
        mac_address = lines[1]
        
        # Membersihkan URL: Stalker API berada di /server/load.php (di luar folder /c/)
        base_url = re.sub(r'/c/?$', '', raw_url).rstrip('/')
        
        print(f"Menghubungkan ke API Portal: {base_url}")
        print(f"Menggunakan MAC Address: {mac_address}")
        
        # HEADER WAJIB: Meniru perangkat MAG Box asli
        headers = {
            "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
            "Cookie": f"mac={mac_address}; stb_lang=en; timezone=GMT",
            "Referer": f"{base_url}/c/",
            "X-User-Agent": "model=MAG250; link=fast"
        }
        
        # 2. Langkah 1: Handshake untuk mendapatkan Token Akses
        handshake_url = f"{base_url}/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml"
        req = requests.get(handshake_url, headers=headers, timeout=15)
        
        try:
            res_json = req.json()
            token = res_json.get('js', {}).get('token')
        except Exception:
            print("Gagal membaca respons API. Server tidak mengembalikan JSON.")
            print("Respons Server:", req.text[:200])
            return
            
        if not token:
            print("Gagal melakukan handshake. Token tidak ditemukan. Periksa kembali kecocokan URL/MAC Anda.")
            return
            
        print("Handshake Berhasil! Token didapatkan.")
        
        # Tambahkan token ke Header untuk otentikasi
        headers["Authorization"] = f"Bearer {token}"
        
        # 3. Langkah 2: Mengambil daftar semua saluran (Channels)
        channels_url = f"{base_url}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
        channels_req = requests.get(channels_url, headers=headers, timeout=20)
        channels_data = channels_req.json().get('js', {}).get('data', [])
        
        if not channels_data:
            print("Daftar siaran kosong atau akun MAC Anda mungkin sudah kedaluwarsa/diblokir.")
            return
            
        # 4. Langkah 3: Menyusun data ke format Playlist M3U yang valid
        with open("playlist.m3u", "w", encoding="utf-8") as m3u:
            m3u.write("#EXTM3U\n")
            count = 0
            for ch in channels_data:
                name = ch.get('name', 'Unknown Channel')
                cmd = ch.get('cmd', '')
                
                if "http" in cmd:
                    stream_url = cmd.replace("ffmpeg ", "").replace("ch/ ", "ch/").strip()
                    m3u.write(f"#EXTINF:-1,{name}\n")
                    m3u.write(f"{stream_url}\n")
                    count += 1
                
        print(f"Sukses! Berhasil mengonversi {count} saluran ke dalam 'playlist.m3u'.")
        
    except FileNotFoundError:
        print("Error: File portal.txt tidak ditemukan di root repositori.")
    except Exception as e:
        print(f"Terjadi masalah pemrosesan Stalker API: {e}")

if __name__ == "__main__":
    fetch_stalker_to_m3u()
