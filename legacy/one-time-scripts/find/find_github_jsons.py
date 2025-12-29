#!/usr/bin/env python3
"""Robust file finder"""
import os
import json

found = []
base = '/home/ubuntu/sofia-pulse'
for root, dirs, files in os.walk(base):
    if 'node_modules' in root or '.git' in root: continue
    for f in files:
        if 'github' in f.lower() and f.endswith('.json'):
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            found.append({'path': path, 'size': size})

with open('found_github_files.json', 'w') as f:
    json.dump(found, f, indent=2)

print(f"Found {len(found)} files. Saved to found_github_files.json")
