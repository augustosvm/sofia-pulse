import shutil
from pathlib import Path

src = Path(r"c:\Users\augusto.moreira\Documents\sofia-pulse\public\data\countries-110m.geojson")
dst_dir = Path(r"c:\Users\augusto.moreira\Documents\sofia-web\public\data")
dst = dst_dir / "countries-110m.geojson"

dst_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(src, dst)

print(f"OK Copied to: {dst}")
print(f"Size: {dst.stat().st_size:,} bytes")

import json
with open(dst) as f:
    data = json.load(f)
    print(f"Features: {len(data['features'])}")
