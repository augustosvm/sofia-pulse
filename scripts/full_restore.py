
import zipfile
import os
import shutil

zip_path = r"c:\Users\augusto.moreira\Documents\sofia-web.zip"
extract_temp = r"c:\Users\augusto.moreira\Documents\sofia-web-restore-full"
target_base = r"c:\Users\augusto.moreira\Documents\sofia-web"

def extract_and_restore():
    # 1. Extract
    print(f"Extracting vital directories from {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            
            # We want everything in src/app/(dashboard) and src/components
            target_files = [
                f for f in all_files 
                if f.startswith("sofia-web/src/app/(dashboard)/") 
                or f.startswith("sofia-web/src/components/")
            ]
            
            print(f"Found {len(target_files)} files to restore.")
            
            for file in target_files:
                zip_ref.extract(file, extract_temp)
                
    except Exception as e:
        print(f"Extraction failed: {e}")
        return

    # 2. Bulk Overwrite
    print("Performing bulk overwrite...")
    
    # Source paths (from extraction)
    src_dashboard = os.path.join(extract_temp, "sofia-web", "src", "app", "(dashboard)")
    src_components = os.path.join(extract_temp, "sofia-web", "src", "components")
    
    # Dest paths (live project)
    dst_dashboard = os.path.join(target_base, "src", "app", "(dashboard)")
    dst_components = os.path.join(target_base, "src", "components")

    # Wipe and Replace Dashboard Pages
    if os.path.exists(dst_dashboard):
        print(f"Wiping {dst_dashboard}")
        shutil.rmtree(dst_dashboard)
    print(f"Restoring {dst_dashboard}")
    shutil.copytree(src_dashboard, dst_dashboard)

    # Wipe and Replace Components (Safety: ensure we have all UI elements)
    if os.path.exists(dst_components):
        print(f"Wiping {dst_components}")
        shutil.rmtree(dst_components)
    print(f"Restoring {dst_components}")
    shutil.copytree(src_components, dst_components)

    print("BULK RESTORATION COMPLETE.")

if __name__ == "__main__":
    extract_and_restore()
