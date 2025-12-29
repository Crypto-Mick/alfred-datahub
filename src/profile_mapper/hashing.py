from pathlib import Path
import hashlib


def sha1_of_file(path: Path) -> str:
    """
    Compute SHA-1 hash of file contents.

    Returns:
        str: hash in format "sha1:<hex>"
    """
    h = hashlib.sha1()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    return "sha1:" + h.hexdigest()
