from PIL import Image


def sanitize_image(image: Image.Image) -> Image.Image:
    R, G, B = image.convert("RGB").split()
    r = R.load()
    g = G.load()
    b = B.load()
    w, h = image.size

    # Convert non-black pixels to white
    for i in range(w):
        for j in range(h):
            if r[i, j] != 255 or g[i, j] != 255 or b[i, j] != 255:
                r[i, j] = 0  # Just change R channel
    # Merge just the R channel as all channels
    im = Image.merge("RGB", (R, R, R))
    return im


queues = {
    "1v1": "1v1 duel",
    "2v2": "2v2 brawl",
    "3v3": "3v3 arcade",
}


def header_tmpl(header_text: str):
    return f"\n======= {header_text} =======\n"


def print_surrounded(header_text: str, body: str):
    footer = f"\n{'='*(len(header_tmpl(header_text))-2)}\n"
    print(f"{header_tmpl(header_text)}{body}{footer}")
