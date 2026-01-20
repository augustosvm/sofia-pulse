
import zipfile
import os
import sys

zip_path = r"c:\Users\augusto.moreira\Documents\sofia-web.zip"
extract_to = r"c:\Users\augusto.moreira\Documents\sofia-web-restore-surgical"

def extract_layout_files():
    if not os.path.exists(zip_path):
        print(f"Error: Zip file not found at {zip_path}")
        return

    print(f"Opening {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            print(f"Total files in zip: {len(all_files)}")
            
            # Filter for vital layout files: src folder and root configs
            target_files = [
                f for f in all_files 
                if f.startswith("sofia-web/src/") 
                or (f.startswith("sofia-web/") and "/" not in f[10:] and (f.endswith(".json") or f.endswith(".ts") or f.endswith(".js") or f.endswith(".css")))
            ]
            
            print(f"Found {len(target_files)} layout/config files to extract.")
            
            for file in target_files:
                # print(f"Extracting {file}...") 
                zip_ref.extract(file, extract_to)
                
            print(f"Extraction complete to {extract_to}")
            
    except zipfile.BadZipFile:
        print("Error: Bad Zip File")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_layout_files()
