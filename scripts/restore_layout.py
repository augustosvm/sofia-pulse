
import shutil
import os

# Paths
backup_base = r"c:\Users\augusto.moreira\Documents\sofia-web-restore-surgical\sofia-web"
current_base = r"c:\Users\augusto.moreira\Documents\sofia-web"

# 1. Restore 'funding' directory
src_funding = os.path.join(backup_base, "src", "app", "(dashboard)", "funding")
dst_funding = os.path.join(current_base, "src", "app", "(dashboard)", "funding")

# 2. Archive 'capital' directory
src_capital = os.path.join(current_base, "src", "app", "(dashboard)", "capital")
dst_capital_archived = os.path.join(current_base, "src", "app", "(dashboard)", "_legacy_capital")

# 3. Restore 'sidebar.tsx'
src_sidebar = os.path.join(backup_base, "src", "components", "layout", "sidebar.tsx")
dst_sidebar = os.path.join(current_base, "src", "components", "layout", "sidebar.tsx")

# 4. Restore 'globals.css'
src_globals = os.path.join(backup_base, "src", "app", "globals.css")
dst_globals = os.path.join(current_base, "src", "app", "globals.css")

def run_restoration():
    print("Starting Surgical Layout Restoration...")

    # Move 'capital' to archive
    if os.path.exists(src_capital):
        if os.path.exists(dst_capital_archived):
            shutil.rmtree(dst_capital_archived)
        print(f"Archiving 'capital' to {dst_capital_archived}...")
        shutil.move(src_capital, dst_capital_archived)
    else:
        print("Warning: 'capital' directory not found, skipping archive.")

    # Copy 'funding' from backup
    if os.path.exists(dst_funding):
        print("Removing existing 'funding' directory (if any)...")
        shutil.rmtree(dst_funding)
    
    if os.path.exists(src_funding):
        print(f"Restoring 'funding' from {src_funding}...")
        shutil.copytree(src_funding, dst_funding)
    else:
        print(f"Error: Backup 'funding' directory not found at {src_funding}")
        return

    # Overwrite sidebar.tsx
    print(f"Restoring sidebar.tsx...")
    shutil.copy2(src_sidebar, dst_sidebar)

    # Overwrite globals.css
    print(f"Restoring globals.css...")
    shutil.copy2(src_globals, dst_globals)

    print("Restoration Complete.")

if __name__ == "__main__":
    run_restoration()
