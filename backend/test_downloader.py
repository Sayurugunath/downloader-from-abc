from downloader import get_video_info


url = input("Paste video URL: ").strip()

print("\nAnalyzing...\n")

info = get_video_info(url)

print("Title:", info["title"])
print("Uploader:", info["uploader"])
print("Duration:", info["duration"], "seconds")

print("\nAvailable formats:\n")

for fmt in info["formats"]:
    print(
        f'{fmt["format_id"]:>5} | '
        f'{str(fmt["resolution"]):>10} | '
        f'{str(fmt["ext"]):>5} | '
        f'video={fmt["vcodec"]} | '
        f'audio={fmt["acodec"]}'
    )