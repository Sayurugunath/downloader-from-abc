from downloader import download_video

url = input("Paste video URL: ").strip()

print("\nStarting download...\n")

download_video(url)

print("\nDownload complete!")