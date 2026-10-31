import os
import sys
import requests
import re
import json

m3u_content = "#EXTM3U\n"
total_all_channels = 0

if not os.path.exists('Portal.txt'):
    print("Error: File Portal.txt tidak ditemukan!")
    sys.exit(1)

with open('Portal.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

if not lines:
    print("Error: File Portal.txt kosong!")
    sys.exit(1)

print(f"Membaca {len(lines)} akun MAC Portal dari file...")

for index, account in enumerate(lines, start=1):
    if '|' not in account:
        print(f"Skipping baris {index}: Format salah (Gunakan URL|MAC)")
        continue
        
    PORTAL_URL, MAC_ADDRESS = account.split('|', 1)
    PORTAL_URL = PORTAL_URL.strip()
    MAC_ADDRESS = MAC_ADDRESS.strip()
    
    print(f"\n[{index}/{len(lines)}] Memproses: {PORTAL_URL}")
    
    # Normalisasi Base URL
    if '/c/' in PORTAL_URL:
        base_url = PORTAL_URL.split('/c/')[0]
    else:
        base_url = PORTAL_URL.rstrip('/')
        
    api_url = f"{base_url}/server/load.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbid/000000000000000000000000000000000000',
        'Cookie': f'mac={MAC_ADDRESS}; stb_lang=en; timezone=Europe%2FParis;',
        'Referer': f"{base_url}/c/",
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    try:
        # 1. Handshake Token
        handshake_url = f"{api_url}?type=stb&action=handshake&token="
        response = requests.get(handshake_url, headers=headers, timeout=12)
        
        if response.status_code == 200:
            try:
                token = response.json().get('js', {}).get('token', '')
                if token:
                    headers['Authorization'] = f"Bearer {token}"
                    print("-> Autentikasi Berhasil!")
            except Exception:
                print("-> Gagal mengurai token handshake, mencoba lanjut...")

        # 2. Ambil Data Kategori Terlebih Dahulu (Penting untuk mapping Grup Kategori)
        genres_url = f"{api_url}?type=itv&action=get_genres"
        genre_mapping = {}
        try:
            genres_res = requests.get(genres_url, headers=headers, timeout=10)
            genres_data = genres_res.json().get('js', [])
            if isinstance(genres_data, list):
                for genre in genres_data:
                    if isinstance(genre, dict) and 'id' in genre and 'title' in genre:
                        genre_mapping[str(genre['id'])] = str(genre['title']).strip()
        except Exception:
            print("-> Gagal memetakan daftar genre, menggunakan nilai fallback.")

        # 3. Tarik Data Semua Saluran
        channels_url = f"{api_url}?type=itv&action=get_all_channels"
        res = requests.get(channels_url, headers=headers, timeout=15)
        raw_text = res.text
        count = 0

        # METODE 1: Parsing JSON Resmi
        try:
            data = json.loads(raw_text)
            channels_list = data.get('js', [])
            
            if isinstance(channels_list, dict):
                channels_list = list(channels_list.values())
                
            if isinstance(channels_list, list) and len(channels_list) > 0:
                for ch in channels_list:
                    if not isinstance(ch, dict):
                        continue
                        
                    name = ch.get('name', 'Unknown Channel').strip()
                    cmd = ch.get('cmd', '')
                    ch_id = str(ch.get('id', '')).strip()
                    logo = ch.get('logo', '')
                    
                    # Cek Kategori (Prioritas: genre_id mapping -> tv_genre_name -> default)
                    category_id = str(ch.get('category_id', ''))
                    if category_id in genre_mapping:
                        ch_group = genre_mapping[category_id]
                    else:
                        ch_group = ch.get('tv_genre_name', '').strip() or f'Portal_{index}'
                    
                    # Bersihkan tanda kutip ganda pada teks agar format atribut M3U tidak rusak
                    safe_name = name.replace('"', "'")
                    safe_group = ch_group.replace('"', "'")
                    
                    # Resolusi Stream URL
                    stream_url = ""
                    if cmd:
                        clean_cmd = str(cmd).replace('\\', '')
                        link_match = re.search(r'(http[s]?://\S+)', clean_cmd)
                        if link_match:
                            stream_url = link_match.group(1).replace('"', '').replace("'", "")
                        else:
                            stream_id = clean_cmd.split('/')[-1].replace('"', '').strip()
                            stream_url = f"{base_url}/live/{MAC_ADDRESS}/555/{stream_id}.ts"
                    
                    if not stream_url:
                        stream_url = f"{base_url}/playlist/live/{ch_id}.ts"
                        
                    # Perbaikan Mutlak URL Logo
                    logo_url = ""
                    if logo:
                        logo_str = str(logo).strip()
                        if logo_str.startswith('http'):
                            logo_url = logo_str
                        else:
                            # Jika nama file logo tidak menyertakan ekstensi gambar bawaan
                            if not any(logo_str.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                                logo_str += '.png'
                            logo_url = f"{base_url}/misc/logos/320/{logo_str}"
                    
                    # Susun format M3U standar industri (Tanpa spasi sebelum koma)
                    # Pola: #EXTINF:-1 tvg-id="X" tvg-name="X" tvg-logo="X" group-title="X",Nama Saluran
                    m3u_line = f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{safe_name}"'
                    if logo_url:
                        m3u_line += f' tvg-logo="{logo_url}"'
                    m3u_line += f' group-title="{safe_group}",{name}\n{stream_url}\n'
                    
                    m3u_content += m3u_line
                    count += 1
        except Exception:
            pass

        # METODE FALLBACK 2: Regular Expression (Cadangan jika JSON gagal total)
        if count == 0:
            matches = re.findall(r'"id"\s*:\s*"([^"]+)"[^}]+?"name"\s*:\s*"([^"]+)"[^}]+?"cmd"\s*:\s*"([^"]+)"', raw_text)
            if matches:
                for ch_id, name, cmd in matches:
                    ch_id = ch_id.strip()
                    name = name.strip()
                    safe_name = name.replace('"', "'")
                    
                    # Ekstraksi genre mentah dari string terdekat jika ada
                    genre_match = re.search(r'"tv_genre_name"\s*:\s*"([^"]+)"', raw_text)
                    ch_group = genre_match.group(1).strip() if genre_match else f'Portal_{index}'
                    safe_group = ch_group.replace('"', "'")
                    
                    clean_cmd = cmd.replace('\\', '')
                    link_match = re.search(r'(http[s]?://\S+)', clean_cmd)
                    if link_match:
                        stream_url = link_match.group(1).replace('"', '').replace("'", "")
                    else:
                        stream_id = clean_cmd.split('/')[-1].replace('"', '').strip()
                        stream_url = f"{base_url}/live/{MAC_ADDRESS}/555/{stream_id}.ts"
                        
                    m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{safe_name}" group-title="{safe_group}",{name}\n{stream_url}\n'
                    count += 1
                    
        print(f"-> Sukses mengekstrak {count} channel dari akun ini.")
        total_all_channels += count

    except Exception as e:
        print(f"-> Gagal memproses portal ini: {e}")
        continue

print(f"\nSelesai! Total keseluruhan: {total_all_channels} channel berhasil dikumpulkan.")

with open('playlist.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u_content)
print("File 'playlist.m3u' diperbarui dengan perbaikan Kategori dan Tvg-Logo!")
