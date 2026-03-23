import os
import zipfile
import tarfile
import py7zr
import rarfile

ARCHIVE_EXTENSIONS = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.tgz', '.tbz2'}


def is_archive(filename):
    """Return True if the filename looks like a supported archive."""
    name = filename.lower()
    for ext in ARCHIVE_EXTENSIONS:
        if name.endswith(ext):
            return True
    return False


def extract_archive(file_path, dest_dir):
    """Extract archive to dest_dir.

    Returns a list of extracted file paths on success,
    or None if password-protected or the format is unsupported/broken.
    """
    name = file_path.lower()
    try:
        if name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Check for password protection on any entry
                for info in zf.infolist():
                    if info.flag_bits & 0x1:
                        return None  # password protected
                zf.extractall(dest_dir)

        elif name.endswith('.7z'):
            with py7zr.SevenZipFile(file_path, mode='r') as sz:
                if sz.needs_password():
                    return None
                sz.extractall(path=dest_dir)

        elif name.endswith('.rar'):
            with rarfile.RarFile(file_path) as rf:
                if rf.needs_password():
                    return None
                rf.extractall(dest_dir)

        elif any(name.endswith(e) for e in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.gz', '.bz2']):
            with tarfile.open(file_path, 'r:*') as tf:
                tf.extractall(dest_dir)

        else:
            return None

    except Exception:
        return None

    extracted = []
    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            extracted.append(os.path.join(root, f))
    return extracted
