import os
from pathlib import Path

# Search for map-related files in sofia-web
web_dir = Path(r"c:\Users\augusto.moreira\Documents\sofia-web")

print("Searching for map files in sofia-web...")
print("="*60)

# Common patterns
patterns = ['*map*.tsx', '*map*.ts', '*Map*.tsx', '*Map*.ts']

for pattern in patterns:
    files = list(web_dir.rglob(pattern))
    if files:
        print(f"\nPattern: {pattern}")
        for f in files:
            rel_path = f.relative_to(web_dir)
            print(f"  {rel_path}")

# Also check app directory structure
app_dir = web_dir / "app"
if app_dir.exists():
    print(f"\nApp directory structure:")
    for item in sorted(app_dir.iterdir()):
        if item.is_dir():
            print(f"  {item.name}/")
