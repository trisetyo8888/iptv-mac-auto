,import requests

# Masukkan URL sumber MAC portal Anda di sini
SOURCE_URL = "http://nk.team-tx.st/c/" 

def fetch_and_save():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        if response.status_code == 200:
            # UBAH DISINI: Ganti portal.txt menjadi playlist.m3u
            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Playlist M3U berhasil diperbarui.")
        else:
            print(f"Gagal mengambil data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    fetch_and_save()
