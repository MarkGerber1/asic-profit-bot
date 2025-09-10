import os

files_to_rename = [
    ("scrapers/asicminervalue.py.txt", "scrapers/asicminervalue.py"),
    ("scrapers/whattomine.py.txt", "scrapers/whattomine.py"),
    ("scrapers/_Init_.py.txt", "scrapers/__init__.py"),
]

for src, dst in files_to_rename:
    try:
        if os.path.exists(src):
            os.rename(src, dst)
            print(f"Renamed: {src} -> {dst}")
        else:
            print(f"File not found: {src}")
    except Exception as e:
        print(f"Error renaming {src} to {dst}: {e}") 