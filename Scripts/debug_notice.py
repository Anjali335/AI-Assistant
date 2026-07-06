from pathlib import Path


def detect_encoding(path, sample_bytes=10000):
    try:
        import chardet
    except Exception:
        return None
    with open(path, "rb") as fh:
        raw = fh.read(sample_bytes)
    res = chardet.detect(raw)
    return res.get("encoding")


def read_lines(path):
    path = Path(path)
    enc = detect_encoding(path)
    tried = []
    # try detected encoding first, then common fallbacks
    for e in ([enc] if enc else []) + ["utf-8", "cp1252", "latin-1"]:
        if not e:
            continue
        tried.append(e)
        try:
            with open(path, "r", encoding=e) as f:
                return [line.rstrip("\n") for line in f]
        except Exception:
            continue
    # last resort: read bytes and decode with replacement to avoid crashes
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode(enc or "utf-8", errors="replace")
    return text.splitlines()


if __name__ == "__main__":
    file = Path(__file__).parent.parent / "processed" / "2023_07.txt"
    lines = read_lines(file)

    for i, line in enumerate(lines[:80]):
        print(i, "=>", repr(line))