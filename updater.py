import os
import requests
import json

def fetch_mac_portal():
    if not os.path.exists('portal.txt'):
        print("File portal.txt tidak ditemukan!")
        return
        
    with open('portal.txt', 'r') as f:
        line = f.readline().strip()
        if not line or '|' not in line:
            return
        portal_url, mac = line.split('|')

    print(f"Memproses Portal: {portal_url} dengan MAC: {mac}")
    
    # Handshake & Get Token / Profile
    handshake_url = f"{portal_url.rstrip('/')}/portal.php?type=stb&action=handshake&js=true"
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
        'Cookie': f'mac={mac}'
    }
    
    try:
        res = requests.get(handshake_url, headers=headers, timeout=10)
        # Meminta data kategori live TV
        ch_url = f"{portal_url.rstrip('/')}/portal.php?type=itv&action=get_all_channels"
        res_ch = requests.get(ch_url, headers=headers, timeout=15)
        data = res_ch.json()
        
        if 'js' in data and 'results' in data['js']:
            channels = data['js']['results']
            
            # Membuat struktur M3U
            with open('playlist.m3u', 'w', encoding='utf-8') as m3u:
                m3u.write("#EXTM3U\n")
                for ch in channels:
                    name = ch.get('name', 'Unknown')
                    cmd = ch.get('cmd', '')
                    # Bersihkan format internal portal cmd
                    if 'ffrt' in cmd:
                        stream_url = cmd.split(' ')[1] if len(cmd.split(' ')) > 1 else cmd
                    else:
                        stream_url = cmd
                        
                    m3u.write(f'#EXTINF:-1 tvg-name="{name}" group-title="MAC Portal",{name}\n')
                    m3u.write(f'{stream_url}\n')
            print("Berhasil membuat playlist.m3u")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    fetch_mac_portal()
