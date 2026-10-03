import requests

def convert_txt_to_m3u():
    try:
        # 1. Membaca URL yang tersimpan di dalam file portal.txt
        with open("portal.txt", "r", encoding="utf-8") as f:
            target_url = f.read().strip()
        
        if not target_url or not target_url.startswith("http"):
            print("Error: Isi portal.txt kosong atau bukan URL yang valid.")
            return

        # 2. Mengunduh data playlist asli dari URL tersebut
        print(f"Mencoba mengambil data dari link: {target_url}")
        response = requests.get(target_url, timeout=15)
        
        if response.status_code == 200:
            # 3. Menyimpan hasilnya langsung ke dalam file playlist.m3u
            with open("playlist.m3u", "w", encoding="utf-8") as m3u_file:
                m3u_file.write(response.text)
            print("Berhasil! playlist.m3u telah dibuat dari link portal.txt.")
        else:
            print(f"Gagal mengunduh. Status server: {response.status_code}")
            
    except FileNotFoundError:
        print("Error: File portal.txt tidak ditemukan di root repositori.")
    except Exception as e:
        print(f"Terjadi kesalahan teknis: {e}")

if __name__ == "__main__":
    convert_txt_to_m3u()
