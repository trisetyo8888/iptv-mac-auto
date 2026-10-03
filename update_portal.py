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
        
        headers = {
            "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
            "Cookie": f"mac={mac_address}; stb_lang=en; timezone=GMT",
            "Referer": f"{base_url}/c/",
            "X-User-Agent": "model=MAG250; link=fast"
        }
        
        # Handshake
        handshake_url = f"{base_url}/server/load.php?type=stb&action=handshake&JsHttpRequest=1-xml"
        req = requests.get(handshake_url, headers=headers, timeout=15)
        token = req.json().get('js', {}).get('token')
        
        if not token:
            print("Gagal melakukan handshake.")
            return
            
        headers["Authorization"] = f"Bearer {token}"
        
        # Mengambil data kategori
        genres_url = f"{base_url}/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml"
        genres_req = requests.get(genres_url, headers=headers, timeout=15)
        genres_data = genres_req.json().get('js', [])
        
        category_map = {}
        if isinstance(genres_data, list):
            for genre in genres_data:
                c_id = str(genre.get('id'))
                c_name = genre.get('title', '').strip()
                if c_name:
                    category_map[c_id] = c_name
                    
        # Mengambil data semua saluran
        channels_url = f"{base_url}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
        channels_req = requests.get(channels_url, headers=headers, timeout=20)
        channels_data = channels_req.json().get('js', {}).get('data', [])
        
        if not channels_data:
            print("Daftar siaran kosong.")
            return
            
        # Menyusun data ke M3U
        with open("playlist.m3u", "w", encoding="utf-8") as m3u:
            m3u.write("#EXTM3U\n")
            count = 0
            for ch in channels_data:
                if ch.get('is_vod') == 1 or ch.get('open') == 0:
                    continue
                    
                name = ch.get('name', 'Unknown Channel').strip()
                cmd = ch.get('cmd', '')
                
                # Mengambil nama folder kategori
                group_name = ch.get('category_name', '').strip()
                if not group_name:
                    cat_id = str(ch.get('tv_genre_id'))
                    group_name = category_map.get(cat_id, "Uncategorized")
                
                # PERBAIKAN: Mengambil data Logo/Icon dari respons server
                logo_val = ch.get('logo', '').strip()
                logo_url = ""
                
                if logo_val:
                    # Jika data logo sudah berupa link web utuh (http/https)
                    if logo_val.startswith("http"):
                        logo_url = logo_val
                    else:
                        # Jika hanya berupa nama berkas gambar, gabungkan dengan URL dasar portal
                        logo_url = f"{base_url}/stalker_portal/misc/logos/{logo_val}"
                
                if "http" in cmd:
                    stream_url = cmd.replace("ffmpeg ", "").replace("ch/ ", "ch/").strip()
                    
                    # Menyusun tag M3U dengan tambahan parameter tvg-logo untuk ikon gambar
                    if logo_url:
                        m3u.write(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="{group_name}",{name}\n')
                    else:
                        m3u.write(f'#EXTINF:-1 group-title="{group_name}",{name}\n')
                        
                    m3u.write(f"{stream_url}\n")
                    count += 1
                
        print(f"Sukses mengonversi {count} saluran dengan penambahan logo gambar.")
        
    except Exception as e:
        print(f"Terjadi masalah: {e}")

if __name__ == "__main__":
    fetch_stalker_to_m3u()
