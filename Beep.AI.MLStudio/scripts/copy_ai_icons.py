"""
Script to copy AI/ML icons from external icon packs to MLStudio's static directory
Run this script to copy all necessary AI/ML icons into the app structure
"""
import shutil
from pathlib import Path
import json

# Base paths
APP_ROOT = Path(__file__).parent.parent
ICON_PACKS_ROOT = Path(r'H:\dev\iconPacks\imgs\AI')
STATIC_IMAGES_DIR = APP_ROOT / 'static' / 'images'
STATIC_AI_ICONS_DIR = STATIC_IMAGES_DIR / 'features' / 'ai-ml'

# AI/ML icon pack mappings
AI_ICON_SOURCES = {
    'ai_general': {
        'source_dir': ICON_PACKS_ROOT / '1766423-artificial-intelligence' / '1766423-artificial-intelligence' / 'png',
        'target_dir': STATIC_AI_ICONS_DIR / 'general',
        'description': 'General AI icons - brain, neural networks, automation (132 icons)'
    },
    'ai_concepts': {
        'source_dir': ICON_PACKS_ROOT / '1985397-ai' / '1985397-ai' / 'png',
        'target_dir': STATIC_AI_ICONS_DIR / 'concepts',
        'description': 'AI concept icons (40 icons)'
    },
    'ai_technology': {
        'source_dir': ICON_PACKS_ROOT / '4541632-artificial-intelligence' / '4541632-artificial-intelligence' / 'png',
        'target_dir': STATIC_AI_ICONS_DIR / 'technology',
        'description': 'AI technology icons (50 icons)'
    },
    'machine_learning': {
        'source_dir': ICON_PACKS_ROOT / '4616700-machine-learning' / '4616700-machine-learning' / 'png',
        'target_dir': STATIC_AI_ICONS_DIR / 'machine-learning',
        'description': 'Machine learning specific icons (50 icons)'
    }
}


def scan_directory_for_png(directory: Path, max_files: int = None, recursive: bool = True) -> list:
    """Scan directory for PNG files (recursively if needed)"""
    png_files = []
    if directory.exists():
        try:
            if recursive:
                pattern = '**/*.png'
            else:
                pattern = '*.png'
            
            for file_path in sorted(directory.glob(pattern)):
                if max_files and len(png_files) >= max_files:
                    break
                png_files.append(file_path.name)
        except Exception as e:
            print(f"Error scanning {directory}: {e}")
    return png_files


def find_file_recursive(directory: Path, filename: str) -> Path:
    """Find a file recursively in directory and subdirectories"""
    # Try exact match first
    exact_match = directory / filename
    if exact_match.exists():
        return exact_match
    
    # Try case-insensitive search recursively
    filename_lower = filename.lower()
    for file_path in directory.rglob('*.png'):
        if file_path.name.lower() == filename_lower:
            return file_path
    
    return None


def copy_ai_icons(category: str, config: dict) -> int:
    """Copy icons for a specific AI/ML category"""
    source_dir = config['source_dir']
    target_dir = config['target_dir']
    
    if not source_dir.exists():
        print(f"[WARNING] Source directory not found for {category}: {source_dir}")
        return 0
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Scan for all PNG files
    icons = scan_directory_for_png(source_dir, max_files=None, recursive=True)
    print(f"   Found {len(icons)} icons in {source_dir.name}")
    
    copied_count = 0
    not_found = []
    
    for icon_name in icons:
        source_file = find_file_recursive(source_dir, icon_name)
        
        if not source_file or not source_file.exists():
            not_found.append(icon_name)
            continue
        
        target_file = target_dir / icon_name
        
        try:
            shutil.copy2(source_file, target_file)
            copied_count += 1
            if copied_count <= 10:  # Print first 10
                print(f"   [OK] Copied: {icon_name}")
            elif copied_count == 11:
                print(f"   [OK] ... (continuing to copy {len(icons) - 10} more icons)")
        except Exception as e:
            print(f"   [ERROR] Failed to copy {icon_name}: {e}")
    
    if not_found:
        print(f"   [WARNING] Not found ({len(not_found)}): {', '.join(not_found[:5])}")
        if len(not_found) > 5:
            print(f"      ... and {len(not_found) - 5} more")
    
    return copied_count


def create_icon_manifest():
    """Create a manifest file listing all copied icons"""
    manifest = {
        'version': '1.0',
        'generated_by': 'copy_ai_icons.py',
        'categories': {}
    }
    
    for category, config in AI_ICON_SOURCES.items():
        target_dir = config['target_dir']
        if target_dir.exists():
            icons = sorted([f.name for f in target_dir.glob('*.png')])
            manifest['categories'][category] = {
                'description': config.get('description', ''),
                'icon_count': len(icons),
                'icons': icons[:20],  # First 20 for reference
                'path': str(target_dir.relative_to(APP_ROOT))
            }
    
    manifest_path = STATIC_IMAGES_DIR / 'ai_icons_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] Icon manifest created: {manifest_path}")
    return manifest_path


def main():
    """Main function to copy all AI/ML icons"""
    print("=" * 60)
    print("Copying AI/ML Icons to MLStudio")
    print("=" * 60)
    print()
    
    total_copied = 0
    for category, config in AI_ICON_SOURCES.items():
        print(f"Copying {category.replace('_', ' ').title()} icons...")
        print(f"   {config.get('description', '')}")
        copied = copy_ai_icons(category, config)
        total_copied += copied
        print(f"   => Copied {copied} icons\n")
    
    # Create manifest
    create_icon_manifest()
    
    print("=" * 60)
    print(f"[SUCCESS] Complete! Copied {total_copied} icons total")
    print("=" * 60)
    print()
    print(f"Icons are now in: {STATIC_AI_ICONS_DIR}")
    print("Manifest file: static/images/ai_icons_manifest.json")


if __name__ == '__main__':
    main()

