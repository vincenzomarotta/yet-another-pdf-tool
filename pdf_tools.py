"""Backend logic for all PDF / image tools.

Pure functions: no UI here. Each raises on hard errors and returns a small
result object (count, path, list) the UI can report on.
"""
import os
import io

import fitz  # PyMuPDF
import qrcode
import numpy as np
from PIL import Image
import imagehash


# --------------------------- previews / info ------------------------------
def pdf_page_count(file):
    """Number of pages in a PDF."""
    with fitz.open(file) as doc:
        return doc.page_count


def render_page_thumb(file, pno=0, max_px=140):
    """Render one PDF page to a PIL RGB thumbnail no larger than max_px."""
    with fitz.open(file) as doc:
        page = doc.load_page(pno)
        r = page.rect
        scale = max_px / max(r.width, r.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


# ----------------------------- PDF: merge ---------------------------------
def merge_pdfs(files, out_path):
    """Merge `files` (list of pdf paths, in order) into `out_path`."""
    if not files:
        raise ValueError("No files selected to merge.")
    out = fitz.open()
    try:
        for f in files:
            with fitz.open(f) as src:
                out.insert_pdf(src)
        out.save(out_path)
    finally:
        out.close()
    return out_path


# ----------------------------- PDF: split ---------------------------------
def parse_ranges(spec, max_page):
    """Parse "1-3,5,7-9" (1-based, inclusive) -> list of 0-based page lists.

    Each comma group becomes one output file.
    """
    groups = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(chunk)
        if start < 1 or end > max_page or start > end:
            raise ValueError(f"Invalid range '{chunk}' (document has {max_page} pages).")
        groups.append(list(range(start - 1, end)))
    if not groups:
        raise ValueError("No valid ranges given.")
    return groups


def split_pdf(file, spec, out_dir):
    """Split `file` into one pdf per range group in `spec`. Returns list of paths."""
    written = []
    with fitz.open(file) as src:
        groups = parse_ranges(spec, src.page_count)
        base = os.path.splitext(os.path.basename(file))[0]
        for n, pages in enumerate(groups, 1):
            out = fitz.open()
            for p in pages:
                out.insert_pdf(src, from_page=p, to_page=p)
            path = os.path.join(out_dir, f"{base} [part {n}].pdf")
            out.save(path)
            out.close()
            written.append(path)
    return written


# ------------------------- PDF: extract images ----------------------------
def extract_images(file, out_dir):
    """Save every embedded raster image from `file` into `out_dir`.

    Returns number of images written.
    """
    count = 0
    base = os.path.splitext(os.path.basename(file))[0]
    with fitz.open(file) as doc:
        for pno in range(doc.page_count):
            for img in doc.get_page_images(pno):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:  # CMYK / other -> convert to RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                path = os.path.join(out_dir, f"{base}_p{pno + 1}_{count + 1}.png")
                pix.save(path)
                pix = None
                count += 1
    if count == 0:
        raise ValueError("No embedded images found in this PDF.")
    return count


# --------------------- PDF: remove duplicate pages ------------------------
def _page_hash(doc, pno, dpi=60):
    """Perceptual hash of a rendered page (low dpi = fast & robust)."""
    pix = doc.load_page(pno).get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return imagehash.phash(img)


def remove_duplicate_pages(file, out_path, threshold=4):
    """Remove near-duplicate consecutive pages (animation-build slides).

    For each run of visually-similar consecutive pages, keep only the LAST one
    (the most complete build). `threshold` = max perceptual-hash hamming
    distance to still count as "same slide" (higher = more aggressive).

    Returns (kept, removed).
    """
    with fitz.open(file) as doc:
        n = doc.page_count
        if n == 0:
            raise ValueError("PDF has no pages.")
        hashes = [_page_hash(doc, p) for p in range(n)]

        keep = []
        for p in range(n):
            # drop this page if the NEXT page is a near-duplicate of it
            if p + 1 < n and (hashes[p] - hashes[p + 1]) <= threshold:
                continue
            keep.append(p)

        out = fitz.open()
        try:
            for p in keep:
                out.insert_pdf(doc, from_page=p, to_page=p)
            out.save(out_path)
        finally:
            out.close()
    return len(keep), n - len(keep)


# ----------------------------- QR generator -------------------------------
def generate_qr(data, out_path, box_size=10, border=4):
    if not data:
        raise ValueError("Nothing to encode.")
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path


# -------------------------- Color palette ---------------------------------
def extract_palette(image_path, n_colors=6):
    """Return list of (hex, (r,g,b)) dominant colors via KMeans."""
    from sklearn.cluster import KMeans

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((400, 400))  # downscale for speed
    pixels = np.asarray(img).reshape(-1, 3)
    km = KMeans(n_clusters=n_colors, n_init=10, random_state=42).fit(pixels)
    centers = np.uint8(km.cluster_centers_)
    # order by cluster size (most common first)
    counts = np.bincount(km.labels_, minlength=n_colors)
    order = np.argsort(counts)[::-1]
    out = []
    for i in order:
        r, g, b = (int(c) for c in centers[i])
        out.append((f"#{r:02X}{g:02X}{b:02X}", (r, g, b)))
    return out


def save_palette_image(colors, out_path, swatch=160):
    """Render a palette (list of (hex, (r,g,b))) to a PNG strip with labels."""
    if not colors:
        raise ValueError("No colors to save.")
    from PIL import ImageDraw, ImageFont
    label_h = 34
    w, h = swatch * len(colors), swatch + label_h
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for i, (hex_code, rgb) in enumerate(colors):
        x0 = i * swatch
        draw.rectangle([x0, 0, x0 + swatch, swatch], fill=rgb)
        # center the hex label under each swatch
        bbox = draw.textbbox((0, 0), hex_code, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + (swatch - tw) / 2, swatch + 8), hex_code,
                  fill="black", font=font)
    img.save(out_path)
    return out_path


def save_palette_text(colors, out_path):
    """Write palette codes (hex + rgb) to a .txt, one color per line."""
    if not colors:
        raise ValueError("No colors to save.")
    lines = [f"{hex_code}  rgb({r}, {g}, {b})" for hex_code, (r, g, b) in colors]
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    return out_path


# --------------------------- shared helpers -------------------------------
def parse_page_list(spec, max_page):
    """Parse "1,3,5-8" (1-based incl.) -> sorted unique 0-based list."""
    out = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(chunk)
        if start < 1 or end > max_page or start > end:
            raise ValueError(f"Invalid page(s) '{chunk}' (doc has {max_page}).")
        out.update(range(start - 1, end))
    if not out:
        raise ValueError("No valid pages given.")
    return sorted(out)


# ----------------------------- PDF: rotate --------------------------------
def rotate_pdf(file, out_path, angle, spec=""):
    """Rotate pages by `angle` (90/180/270). Empty spec = all pages."""
    if angle % 90 != 0:
        raise ValueError("Angle must be 90, 180 or 270.")
    with fitz.open(file) as doc:
        targets = (parse_page_list(spec, doc.page_count) if spec.strip()
                   else range(doc.page_count))
        for p in targets:
            page = doc.load_page(p)
            page.set_rotation((page.rotation + angle) % 360)
        doc.save(out_path)
    return out_path


# ---------------------------- PDF: compress -------------------------------
def compress_pdf(file, out_path):
    """Re-save with object cleanup + deflate. Returns (before, after) bytes."""
    before = os.path.getsize(file)
    with fitz.open(file) as doc:
        doc.save(out_path, garbage=4, deflate=True, clean=True)
    return before, os.path.getsize(out_path)


# -------------------------- PDF -> page images ----------------------------
def pdf_to_images(file, out_dir, dpi=150):
    """Render each page to a PNG. Returns number written."""
    base = os.path.splitext(os.path.basename(file))[0]
    with fitz.open(file) as doc:
        for pno in range(doc.page_count):
            pix = doc.load_page(pno).get_pixmap(dpi=dpi)
            pix.save(os.path.join(out_dir, f"{base}_p{pno + 1}.png"))
        n = doc.page_count
    return n


# ----------------------------- watermark ----------------------------------
def watermark_pdf(file, out_path, text):
    """Stamp diagonal gray `text` across every page."""
    if not text:
        raise ValueError("Watermark text is empty.")
    with fitz.open(file) as doc:
        for page in doc:
            rect = page.rect
            pivot = fitz.Point(rect.width / 2, rect.height / 2)
            page.insert_text(
                fitz.Point(rect.width * 0.18, rect.height * 0.55),
                text, fontsize=46, color=(0.7, 0.7, 0.7),
                morph=(pivot, fitz.Matrix(45)), overlay=True)
        doc.save(out_path)
    return out_path


# ---------------------------- reorder pages -------------------------------
def reorder_pdf(file, out_path, spec):
    """spec = explicit new order "3,1,2" (1-based). Pages may repeat/drop."""
    with fitz.open(file) as doc:
        order = []
        for chunk in spec.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            n = int(chunk)
            if n < 1 or n > doc.page_count:
                raise ValueError(f"Page {n} out of range (1-{doc.page_count}).")
            order.append(n - 1)
        if not order:
            raise ValueError("Enter a page order, e.g. 3,1,2.")
        doc.select(order)
        doc.save(out_path)
    return out_path


# ----------------------------- delete pages -------------------------------
def delete_pages(file, out_path, spec):
    """Remove pages in `spec`, keep the rest. Returns (kept, removed)."""
    with fitz.open(file) as doc:
        drop = set(parse_page_list(spec, doc.page_count))
        keep = [p for p in range(doc.page_count) if p not in drop]
        if not keep:
            raise ValueError("That would delete every page.")
        doc.select(keep)
        doc.save(out_path)
    return len(keep), len(drop)


# --------------------------- images -> PDF --------------------------------
def images_to_pdf(files, out_path):
    """Combine images (in order) into one PDF, one image per page."""
    if not files:
        raise ValueError("No images selected.")
    out = fitz.open()
    try:
        for img in files:
            with fitz.open(img) as idoc:
                pdfbytes = idoc.convert_to_pdf()
            with fitz.open("pdf", pdfbytes) as ipdf:
                out.insert_pdf(ipdf)
        out.save(out_path)
    finally:
        out.close()
    return out_path


# ----------------------------- encrypt ------------------------------------
def encrypt_pdf(file, out_path, password):
    """Password-protect with AES-256 (same pw for open + owner)."""
    if not password:
        raise ValueError("Password is empty.")
    with fitz.open(file) as doc:
        doc.save(out_path, encryption=fitz.PDF_ENCRYPT_AES_256,
                 owner_pw=password, user_pw=password)
    return out_path


# --------------------------- add page numbers -----------------------------
def add_page_numbers(file, out_path):
    """Stamp '1', '2', … centered at the bottom of each page."""
    with fitz.open(file) as doc:
        for i, page in enumerate(doc, 1):
            rect = page.rect
            page.insert_text(
                fitz.Point(rect.width / 2 - 6, rect.height - 24),
                str(i), fontsize=12, color=(0, 0, 0), overlay=True)
        doc.save(out_path)
    return out_path


# ----------------------------- extract text -------------------------------
def extract_text(file, out_path):
    """Dump all page text to a .txt. Returns character count."""
    chunks = []
    with fitz.open(file) as doc:
        for page in doc:
            chunks.append(page.get_text())
    text = "\n".join(chunks)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(text)
    return len(text)


# ----------------------------- HTML -> PDF --------------------------------
def html_to_pdf(source, out_path, page="a4"):
    """Convert an HTML file, a URL, or a raw HTML string to a PDF.

    Local files resolve their images/CSS relative to the file's folder.
    Returns number of pages written.
    """
    archive = None
    if source.startswith(("http://", "https://")):
        import urllib.request
        with urllib.request.urlopen(source, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    elif os.path.isfile(source):
        with open(source, "r", encoding="utf-8", errors="replace") as fp:
            html = fp.read()
        archive = fitz.Archive(os.path.dirname(os.path.abspath(source)))
    else:
        html = source  # treat as raw HTML markup
    if not html.strip():
        raise ValueError("Nothing to convert — source is empty.")

    story = fitz.Story(html=html, archive=archive)
    writer = fitz.DocumentWriter(out_path)
    mediabox = fitz.paper_rect(page)
    where = mediabox + (36, 36, -36, -36)  # 0.5" margins
    pages, more = 0, 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        pages += 1
    writer.close()
    return pages


# ----------------------------- resize image -------------------------------
def resize_image(path, out_path, mode, value):
    """Resize an image. mode = 'percent' | 'width' | 'height' | 'longest'.

    Aspect ratio is always kept. Returns ((old_w, old_h), (new_w, new_h)).
    """
    if value <= 0:
        raise ValueError("Value must be a positive number.")
    img = Image.open(path)
    ow, oh = img.size
    if mode == "percent":
        scale = value / 100.0
        nw, nh = round(ow * scale), round(oh * scale)
    elif mode == "width":
        nw = int(value); nh = round(oh * nw / ow)
    elif mode == "height":
        nh = int(value); nw = round(ow * nh / oh)
    elif mode == "longest":
        scale = value / max(ow, oh)
        nw, nh = round(ow * scale), round(oh * scale)
    else:
        raise ValueError(f"Unknown mode '{mode}'.")
    nw, nh = max(1, nw), max(1, nh)
    resized = img.resize((nw, nh), Image.LANCZOS)
    if resized.mode in ("RGBA", "P") and out_path.lower().endswith((".jpg", ".jpeg")):
        resized = resized.convert("RGB")  # JPEG has no alpha
    resized.save(out_path)
    return (ow, oh), (nw, nh)


# ------------------------------- crop image -------------------------------
def crop_image(path, out_path, box):
    """Crop to box=(left, top, right, bottom) in original pixels. Returns
    the new (width, height)."""
    img = Image.open(path)
    l, t, r, b = (int(round(v)) for v in box)
    l, t = max(0, l), max(0, t)
    r, b = min(img.width, r), min(img.height, b)
    if r - l < 1 or b - t < 1:
        raise ValueError("Crop area is empty — drag a bigger box.")
    cropped = img.crop((l, t, r, b))
    if cropped.mode in ("RGBA", "P") and out_path.lower().endswith((".jpg", ".jpeg")):
        cropped = cropped.convert("RGB")
    cropped.save(out_path)
    return cropped.size


# --------------------------- compress image -------------------------------
def compress_image(path, out_path, quality=70):
    """Shrink an image. JPEG/WebP use `quality` (lossy); PNG is optimized
    losslessly. Returns (before_bytes, after_bytes)."""
    before = os.path.getsize(path)
    img = Image.open(path)
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(out_path, "JPEG", quality=quality, optimize=True,
                 progressive=True)
    elif ext == ".webp":
        img.save(out_path, "WEBP", quality=quality, method=6)
    elif ext == ".png":
        img.save(out_path, "PNG", optimize=True)  # lossless
    else:
        img.save(out_path)
    return before, os.path.getsize(out_path)


# --------------------------- watermark image ------------------------------
def watermark_image(path, out_path, text, opacity=0.30):
    """Stamp diagonal gray `text` across the center of an image.

    opacity is 0..1. Returns out_path.
    """
    if not text:
        raise ValueError("Watermark text is empty.")
    from PIL import ImageDraw, ImageFont
    base = Image.open(path).convert("RGBA")
    w, h = base.size
    alpha = max(0, min(255, int(opacity * 255)))

    size = max(20, int(w / max(8, len(text)) * 1.4))
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except Exception:
        font = ImageFont.load_default()

    # draw text onto its own tight layer, then rotate and center it
    tmp = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    txt = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((10 - bbox[0], 10 - bbox[1]), text,
                             font=font, fill=(128, 128, 128, alpha))
    txt = txt.rotate(45, expand=True)

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(txt, ((w - txt.width) // 2, (h - txt.height) // 2), txt)
    out = Image.alpha_composite(base, layer)

    if out_path.lower().endswith((".jpg", ".jpeg")):
        out = out.convert("RGB")
    out.save(out_path)
    return out_path


# --------------------------- convert image format -------------------------
def convert_image(path, out_path):
    """Convert an image to another format (inferred from out_path extension).

    Handles JPEG having no alpha (flattens onto white). Returns out_path.
    """
    img = Image.open(path)
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        if img.mode in ("RGBA", "LA", "P"):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1])  # composite over white
            img = bg
        else:
            img = img.convert("RGB")
    img.save(out_path)
    return out_path
