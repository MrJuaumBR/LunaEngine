import sys, os, shutil
from pathlib import Path

base_fldr = Path(os.path.dirname(__file__)).parent

def walkThroughPycache(folder: Path):
    removed = 0 
    for item in folder.iterdir():
        if item.is_dir():
            if item.name == "__pycache__":
                print(f"Removing {item}")
                for file in item.iterdir():
                    file.unlink()
                os.chmod(item, 0o777)  # Ensure we have permissions to delete
                shutil.rmtree(item)
                removed += 1
            else:
                removed += walkThroughPycache(item)
                
    return removed
                
if __name__ == '__main__':
    rm = walkThroughPycache(base_fldr)
    print(f"Total items removed: {rm}")
