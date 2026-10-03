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
            
        raw_url = lines[0]
        mac_address = lines[1]
        
        base_url = re.sub(r'/c/?$', '', raw_url).rstrip('/')
        
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
            token = req.json().get('js', {}).get('token')
        except Exception:
            print("Gagal membaca respons API. Server tidak mengembalikan JSON.")
            return
            
        if not token:
            print("Gagal melakukan handshake. Token tidak ditemukan.")
            return
            
        headers["Authorization"] = f"Bearer {token}"
        
        # 3. Langkah 2: Mengambil DAFTAR KATEGORI/GENRE terlebih dahulu (Agar punya nama folder)
        genres_url = f"{base_url}/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml"
        genres_req = requests.get(genres_url, headers=headers, timeout=15)
        genres_data = genres_req.json().get('js', [])
        
        # Simpan kategori ke dalam kamus (dictionary) ID -> Nama Kategori
        category_map = {}
        for genre in genres_data:
            c_id = str(genre.get('id'))
            c_name = genre.get('title', 'Lainnya')
            category_map[c_id] = c_name
            
        # 4. Langkah 3: Mengambil semua daftar saluran
        channels_url = f"{base_url}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
        channels_req = requests.get(channels_url, headers=headers, timeout=20)
        channels_data = channels_req.json().get('js', {}).get('data', [])
        
        if not channels_data:
            print("Daftar siaran kosong.")
            return
            
        # 5. Langkah 4: Menyusun data ke format M3U terstruktur
        with open("playlist.m3u", "w", encoding="utf-8") as m3u:
            m3u.write("#EXTM3U\n")
            count = 0
            for ch in channels_data:
                # FILTER UTAMA: Hanya TV Live, abaikan data Film/VOD/Drama agar playlist ringan
                if ch.get('is_vod') == 1 or ch.get('open') == 0:
                    continue
                    
                name = ch.get('name', 'Unknown Channel')
                cmd = ch.get('cmd', '')
                
                # Menentukan nama folder kategori berdasarkan ID-nya
                cat_id = str(ch.get('tv_genre_id'))
                group_name = category_map.get(cat_id, "Uncategorized")
                
                if "http" in cmd:
                    stream_url = cmd.replace("ffmpeg ", "").replace("ch/ ", "ch/").strip()
                    # Menambahkan tag group-title agar aplikasi IPTV mendeteksi folder kategori
                    m3u.write(f'#EXTINF:-1 group-title="{group_name}",{name}\n')
                    m3u.write(f"{stream_url}\n")
                    count += 1
                
        print(f"Sukses! Mengonversi {count} saluran ke playlist.m3u dengan pembagian folder otomatis.")
        
    except FileNotFoundError:
        print("Error: File portal.txt tidak ditemukan.")
    except Exception as e:
        print(f"Terjadi masalah: {e}")

if __name__ == "__main__":
    fetch_stalker_to_m3u()
