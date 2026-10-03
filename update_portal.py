import requests

# URL sumber MAC portal yang selalu berubah atau menyediakan data terbaru
SOURCE_URL = "http://nk.team-tx.st/c/" 

def fetch_and_save():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        if response.status_code == 200:
            # Simpan hasilnya ke file portal.txt
            with open("portal.txt", "w") as f:
                f.write(response.text)
            print("Portal berhasil diperbarui.")
        else:
            print(f"Gagal mengambil data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    fetch_and_save()
