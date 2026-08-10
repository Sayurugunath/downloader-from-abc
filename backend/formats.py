def format_size(size):
    if not size:
        return None

    size = float(size)

    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

    return f"{size / (1024 * 1024):.1f} MB"


def get_size(fmt):
    return fmt.get("filesize") or fmt.get("filesize_approx")


def video_score(fmt):
    """
    Higher score = better choice.

    We prefer:
    1. MP4
    2. H.264
    3. Video + audio
    4. Higher resolution
    """

    ext = (fmt.get("ext") or "").lower()
    vcodec = (fmt.get("vcodec") or "").lower()
    acodec = (fmt.get("acodec") or "").lower()

    resolution = fmt.get("resolution") or ""

    try:
        height = int(resolution.split("x")[1])
    except (ValueError, IndexError):
        height = 0

    score = 0

    # Container preference
    if ext == "mp4":
        score += 100

    elif ext == "webm":
        score += 50

    # Codec preference
    if vcodec.startswith("avc1"):
        score += 100

    elif vcodec.startswith("av01"):
        score += 60

    elif vcodec.startswith("vp9"):
        score += 50

    # Formats with audio are convenient
    if acodec and acodec != "none":
        score += 30

    # Resolution
    score += height

    return score


def clean_formats(formats):

    video_by_quality = {}

    audio_formats = {}

    # ------------------------------------------
    # FIND VIDEO FORMATS
    # ------------------------------------------

    for fmt in formats:

        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")
        ext = (fmt.get("ext") or "").lower()

        resolution = fmt.get("resolution") or ""

        if vcodec in (None, "none"):
            continue

        if "x" not in resolution:
            continue

        if ext not in ("mp4", "webm", "mkv"):
            continue

        try:
            height = int(
                resolution.split("x")[1]
            )
        except (ValueError, IndexError):
            continue

        quality = f"{height}p"

        score = video_score(fmt)

        current = video_by_quality.get(
            quality
        )

        if current is None:

            video_by_quality[quality] = (
                score,
                fmt
            )

        elif score > current[0]:

            video_by_quality[quality] = (
                score,
                fmt
            )


    # ------------------------------------------
    # FIND AUDIO FORMATS
    # ------------------------------------------

    for fmt in formats:

        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")

        if vcodec not in (None, "none"):
            continue

        if not acodec or acodec == "none":
            continue

        ext = (
            fmt.get("ext") or
            "unknown"
        ).lower()

        size = get_size(fmt)

        # Keep the largest/best format per extension
        current = audio_formats.get(ext)

        if current is None:

            audio_formats[ext] = fmt

        elif (
            get_size(fmt) or 0
        ) > (
            get_size(current) or 0
        ):

            audio_formats[ext] = fmt


    # ------------------------------------------
    # BUILD QUALITY LIST
    # ------------------------------------------

    qualities = []

    for quality, (_, fmt) in video_by_quality.items():

        ext = (
            fmt.get("ext") or
            "unknown"
        ).lower()

        acodec = fmt.get("acodec")

        format_id = fmt.get(
            "format_id"
        )

        # Video already contains audio
        if acodec and acodec != "none":

            selector = format_id
            needs_merge = False

        else:

            # Video-only format.
            # yt-dlp will select the best audio.
            selector = (
                f"{format_id}+bestaudio"
            )

            needs_merge = True


        qualities.append({

            "quality": quality,

            "format": ext.upper(),

            "size": format_size(
                get_size(fmt)
            ),

            "format_id": format_id,

            "selector": selector,

            "needs_merge": needs_merge,

            "codec": fmt.get(
                "vcodec"
            ),

        })


    # Highest resolution first
    qualities.sort(
        key=lambda item:
            int(
                item["quality"]
                .replace("p", "")
            ),
        reverse=True
    )


    # ------------------------------------------
    # AUDIO LIST
    # ------------------------------------------

    audio = []

    for ext, fmt in audio_formats.items():

        audio.append({

            "format": ext.upper(),

            "size": format_size(
                get_size(fmt)
            ),

            "format_id": fmt.get(
                "format_id"
            ),

        })


    return {

        "qualities": qualities,

        "audio": audio,

    }