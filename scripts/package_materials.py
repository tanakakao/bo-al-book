"""Build the reader download that accompanies the HTML book."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "downloads/BO_AL_book_vol1_materials.zip"


def files():
    yield ROOT / "editorial/MATERIALS_README.md", "README.md"
    yield ROOT / "requirements.txt", "requirements.txt"
    yield ROOT / "LICENSE.md", "LICENSE.md"
    yield ROOT / "LICENSES/BSD-3-Clause.txt", "LICENSES/BSD-3-Clause.txt"
    for directory, patterns in [
        ("notebooks", ("*.ipynb", "*.py")),
        ("data", ("*.csv",)),
        ("quality", ("ch*_metrics.json",)),
    ]:
        for pattern in patterns:
            for path in sorted((ROOT / directory).glob(pattern)):
                yield path, path.relative_to(ROOT).as_posix()


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUTPUT, "w") as archive:
        for path, name in files():
            entry = ZipInfo("BO_AL_book_vol1_materials/" + name)
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes())


if __name__ == "__main__":
    main()
