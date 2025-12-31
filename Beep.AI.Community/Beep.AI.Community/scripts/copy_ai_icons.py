"""
Script to copy AI/ML icons from external icon packs to the application's static directory
Run this script to copy all necessary AI/ML icons into the app structure
"""
import shutil
from pathlib import Path

# Base paths
APP_ROOT = Path(__file__).parent.parent
ICON_PACKS_ROOT = Path(r'H:\dev\iconPacks\imgs')
STATIC_ICONS_DIR = APP_ROOT / 'static' / 'assets' / 'icons'
STATIC_IMAGES_DIR = APP_ROOT / 'static' / 'assets' / 'images'

# AI/ML icon sources
AI_ICON_SOURCES = [
    {
        'name': 'AI General',
        'source_dir': ICON_PACKS_ROOT / 'AI' / '1766423-artificial-intelligence' / '1766423-artificial-intelligence' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'ai-ml',
        'max_files': 50
    },
    {
        'name': 'Machine Learning',
        'source_dir': ICON_PACKS_ROOT / 'AI' / '4616700-machine-learning' / '4616700-machine-learning' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'ai-ml',
        'max_files': 50
    },
    {
        'name': 'AI Pack 2',
        'source_dir': ICON_PACKS_ROOT / 'AI' / '1985397-ai' / '1985397-ai' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'ai-ml',
        'max_files': 40
    },
    {
        'name': 'AI Pack 3',
        'source_dir': ICON_PACKS_ROOT / 'AI' / '4541632-artificial-intelligence' / '4541632-artificial-intelligence' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'ai-ml',
        'max_files': 50
    }
]

# Competition/Winning icons
COMPETITION_ICON_SOURCES = [
    {
        'name': 'Winning/Competition',
        'source_dir': ICON_PACKS_ROOT / '1021175-winning' / '1021175-winning' / 'png',
        'target_dir': STATIC_IMAGES_DIR / 'features' / 'competitions',
        'max_files': 50
    }
]


def copy_icons_from_source(source_config: dict) -> int:
    """Copy icons from a source directory to target directory"""
    source_dir = source_config['source_dir']
    target_dir = source_config['target_dir']
    max_files = source_config.get('max_files', 50)
    name = source_config['name']
    
    if not source_dir.exists():
        print(f"   [WARNING] Source directory not found: {source_dir}")
        return 0
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PNG files
    png_files = sorted(list(source_dir.glob('*.png')))
    
    if not png_files:
        print(f"   [WARNING] No PNG files found in {source_dir}")
        return 0
    
    copied_count = 0
    for png_file in png_files[:max_files]:
        target_file = target_dir / png_file.name
        
        # Skip if file already exists (unless we want to overwrite)
        if target_file.exists():
            continue
        
        try:
            shutil.copy2(png_file, target_file)
            copied_count += 1
        except Exception as e:
            print(f"   [ERROR] Failed to copy {png_file.name}: {e}")
    
    print(f"   [OK] Copied {copied_count} icons from {name}")
    return copied_count


def main():
    """Main function to copy all AI/ML and competition icons"""
    print("=" * 60)
    print("Copying AI/ML and Competition Icons to Application")
    print("=" * 60)
    print()
    
    total_copied = 0
    
    # Copy AI/ML icons
    print("1. Copying AI/ML icons...")
    for source_config in AI_ICON_SOURCES:
        copied = copy_icons_from_source(source_config)
        total_copied += copied
    
    print()
    
    # Copy competition icons
    print("2. Copying Competition/Winning icons...")
    for source_config in COMPETITION_ICON_SOURCES:
        copied = copy_icons_from_source(source_config)
        total_copied += copied
    
    print()
    print("=" * 60)
    print(f"[SUCCESS] Complete! Copied {total_copied} icons total")
    print("=" * 60)
    print()
    print(f"AI/ML icons are now in: {STATIC_ICONS_DIR / 'ai-ml'}")
    print(f"Competition icons are now in: {STATIC_IMAGES_DIR / 'features' / 'competitions'}")


if __name__ == '__main__':
    main()

