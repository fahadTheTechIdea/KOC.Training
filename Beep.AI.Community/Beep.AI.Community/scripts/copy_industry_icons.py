"""
Script to copy industry icons from external icon packs to the application's static directory
Run this script to copy all necessary icons into the app structure
"""
import shutil
from pathlib import Path
import os

# Base paths
APP_ROOT = Path(__file__).parent.parent
ICON_PACKS_ROOT = Path(r'H:\dev\iconPacks\imgs')
STATIC_ICONS_DIR = APP_ROOT / 'static' / 'assets' / 'icons'
STATIC_IMAGES_DIR = APP_ROOT / 'static' / 'assets' / 'images'

# Industry icon mappings
INDUSTRY_ICON_SOURCES = {
    'oil_gas': {
        'source_dir': ICON_PACKS_ROOT / '5725015-oil-and-petroleum' / '5725015-oil-and-petroleum' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'oil_gas',
        'icons': [],  # Auto-scan - will copy all PNG files from new oil & gas packs
        'fallback_dirs': [
            Path(r'H:\dev\iconPacks\oilandgas32mycollection\png'),  # Keep old path as fallback
            ICON_PACKS_ROOT / '6315514-oil-and-gas-industry',
            ICON_PACKS_ROOT / '7258558-oil-and-gas-industry'
        ]
    },
    'health_medical': {
        'source_dir': ICON_PACKS_ROOT / '3254044-laboratory' / '3254044-laboratory' / 'png',
        'target_dir': STATIC_ICONS_DIR / 'health_medical',
        'icons': [],  # Auto-scan - will copy all PNG files
        'fallback_dirs': [
            ICON_PACKS_ROOT / '4482096-health-insurance'
        ]
    },
    'energy_sustainability': {
        'source_dir': ICON_PACKS_ROOT / '4514697-renewable-energy',
        'target_dir': STATIC_ICONS_DIR / 'energy_sustainability',
        'icons': [],  # Auto-scan - will copy all PNG files
        'fallback_dirs': [
            ICON_PACKS_ROOT / '4545243-nuclear-energy',
            ICON_PACKS_ROOT / '4815152-sustainable-energy',
            ICON_PACKS_ROOT / '6629098-smart-meters'
        ]
    },
    'industrial': {
        'source_dir': ICON_PACKS_ROOT / '1064238-industrial-process',
        'target_dir': STATIC_ICONS_DIR / 'industrial',
        'icons': [],  # Auto-scan - will copy all PNG files
        'fallback_dirs': []
    },
    'competitions': {
        'source_dir': ICON_PACKS_ROOT / '1021175-winning' / '1021175-winning' / 'png',
        'target_dir': STATIC_IMAGES_DIR / 'features' / 'competitions',
        'icons': [],  # Auto-scan - will copy all PNG files (trophies, medals, winners)
        'fallback_dirs': []
    },
    'leadership': {
        'source_dir': ICON_PACKS_ROOT / '9512427-leadership' / '9512427-leadership' / 'png',
        'target_dir': STATIC_IMAGES_DIR / 'features' / 'leadership',
        'icons': [],  # Auto-scan - will copy all PNG files (teamwork, certificates, mentoring)
        'fallback_dirs': []
    },
    'finance': {
        'source_dir': ICON_PACKS_ROOT / 'BusinessandFinance',
        'target_dir': STATIC_ICONS_DIR / 'finance',
        'icons': []  # Auto-scan recursively - will copy first 20 PNG files
    },
    'healthcare': {
        'source_dir': ICON_PACKS_ROOT / 'healthcare',
        'target_dir': STATIC_ICONS_DIR / 'healthcare',
        'icons': []  # Auto-scan recursively - will copy first 20 PNG files
    },
    'real_estate': {
        'source_dir': ICON_PACKS_ROOT / 'real-estate',
        'target_dir': STATIC_ICONS_DIR / 'real_estate',
        'icons': []  # Auto-scan recursively - will copy first 20 PNG files
    },
    'retail': {
        'source_dir': ICON_PACKS_ROOT / '1198327-retail',
        'target_dir': STATIC_ICONS_DIR / 'retail',
        'icons': []  # Auto-scan - multiple retail packs available
    },
    'manufacturing': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',
        'target_dir': STATIC_ICONS_DIR / 'manufacturing',
        'icons': []  # Auto-scan - using timing pack for industrial/manufacturing icons
    },
    'education': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback to timing, or create generic
        'target_dir': STATIC_ICONS_DIR / 'education',
        'icons': []  # Auto-scan or use generic icons
    },
    'agriculture': {
        'source_dir': ICON_PACKS_ROOT / '4479880-agriculture',
        'target_dir': STATIC_ICONS_DIR / 'agriculture',
        'icons': []  # Auto-scan - multiple agriculture packs available
    },
    'transportation': {
        'source_dir': ICON_PACKS_ROOT / '1493652-logistics',
        'target_dir': STATIC_ICONS_DIR / 'transportation',
        'icons': []  # Auto-scan - multiple logistics/transportation packs
    },
    'energy': {
        'source_dir': ICON_PACKS_ROOT / '4514697-renewable-energy',
        'target_dir': STATIC_ICONS_DIR / 'energy',
        'icons': []  # Auto-scan - multiple energy packs available
    },
    'insurance': {
        'source_dir': ICON_PACKS_ROOT / '2646182-insurance',
        'target_dir': STATIC_ICONS_DIR / 'insurance',
        'icons': []  # Auto-scan - multiple insurance packs available
    },
    'telecom': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback
        'target_dir': STATIC_ICONS_DIR / 'telecom',
        'icons': []  # Auto-scan or use generic
    },
    'media': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback
        'target_dir': STATIC_ICONS_DIR / 'media',
        'icons': []  # Auto-scan or use generic
    },
    'government': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback
        'target_dir': STATIC_ICONS_DIR / 'government',
        'icons': []  # Auto-scan or use generic
    },
    'sports': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback
        'target_dir': STATIC_ICONS_DIR / 'sports',
        'icons': []  # Auto-scan or use generic
    },
    'food_beverage': {
        'source_dir': ICON_PACKS_ROOT / '4070563-timing',  # Fallback
        'target_dir': STATIC_ICONS_DIR / 'food_beverage',
        'icons': []  # Auto-scan or use generic
    },
    'general': {
        'source_dir': APP_ROOT / 'static' / 'assets' / 'images',
        'target_dir': STATIC_ICONS_DIR / 'general',
        'icons': [
            'SimpleInfoApps.png'
        ]
    }
}


def scan_directory_for_png(directory: Path, max_files: int = 20, recursive: bool = True) -> list:
    """Scan directory for PNG files (recursively if needed)"""
    png_files = []
    if directory.exists():
        try:
            if recursive:
                # Search recursively in subdirectories
                pattern = '**/*.png'
            else:
                # Only search in the directory itself
                pattern = '*.png'
            
            for file_path in sorted(directory.glob(pattern)):
                if len(png_files) >= max_files:
                    break
                # Store relative path from directory to preserve subdirectory structure if needed
                # But for now, just use filename
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


def copy_icons(industry: str, config: dict) -> int:
    """Copy icons for a specific industry"""
    source_dir = config['source_dir']
    target_dir = config['target_dir']
    icons = config['icons']
    
    # Handle multiple possible source directories for industries with multiple packs
    possible_dirs = [source_dir]
    
    # Add fallback directories for industries with multiple icon pack options
    if industry == 'retail':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '1326494-retail',
            ICON_PACKS_ROOT / '4293054-retail',
            ICON_PACKS_ROOT / '4379529-supermarket',
            ICON_PACKS_ROOT / '4536642-sales',
            ICON_PACKS_ROOT / '4543149-online-shopping',
            ICON_PACKS_ROOT / '4544380-online-shopping',
            ICON_PACKS_ROOT / '4564267-ecommerce',
            ICON_PACKS_ROOT / '4601616-ecommerce',
            ICON_PACKS_ROOT / '4601637-ecommerce',
            ICON_PACKS_ROOT / '4801130-ecommerce'
        ])
    elif industry == 'agriculture':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '4584950-farming',
            ICON_PACKS_ROOT / '4590727-smart-farm',
            ICON_PACKS_ROOT / '4752022-irrigation'
        ])
    elif industry == 'transportation':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '4320169-logistic-delivery',
            ICON_PACKS_ROOT / '4598554-logistics',
            ICON_PACKS_ROOT / '4693426-aviation',
            ICON_PACKS_ROOT / '4693433-aviation',
            ICON_PACKS_ROOT / '4549850-travel'
        ])
    elif industry == 'energy':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '4545243-nuclear-energy',
            ICON_PACKS_ROOT / '4549377-battery',
            ICON_PACKS_ROOT / '4815152-sustainable-energy',
            ICON_PACKS_ROOT / '6629098-smart-meters'
        ])
    elif industry == 'oil_gas':
        # Add fallback directories for oil & gas
        if 'fallback_dirs' in config:
            possible_dirs.extend(config['fallback_dirs'])
    elif industry == 'health_medical':
        # Add fallback directories for health/medical
        if 'fallback_dirs' in config:
            possible_dirs.extend(config['fallback_dirs'])
    elif industry == 'energy_sustainability':
        # Add fallback directories for energy/sustainability
        if 'fallback_dirs' in config:
            possible_dirs.extend(config['fallback_dirs'])
    elif industry in ['competitions', 'leadership']:
        # These use feature directories, no fallbacks needed
        pass
    elif industry == 'insurance':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '4482096-health-insurance',
            ICON_PACKS_ROOT / '4485938-insurance',
            ICON_PACKS_ROOT / '4599211-insurance'
        ])
    elif industry == 'real_estate':
        possible_dirs.extend([
            ICON_PACKS_ROOT / '1011798-real-estate',
            ICON_PACKS_ROOT / '9676753-real-estate'
        ])
    
    # Find first existing directory
    primary_source_dir = None
    for possible_dir in possible_dirs:
        if possible_dir.exists():
            primary_source_dir = possible_dir
            break
    
    if not primary_source_dir or not primary_source_dir.exists():
        print(f"[WARNING] Source directory not found for {industry}: {possible_dirs[0]}")
        return 0
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # If icons list is empty, scan the directory recursively
    if not icons:
        # For special categories, scan more files
        max_files = 50 if industry in ['competitions', 'leadership', 'oil_gas', 'health_medical', 'energy_sustainability'] else 20
        icons = scan_directory_for_png(primary_source_dir, max_files=max_files, recursive=True)
        print(f"   Auto-scanned {len(icons)} icons from {primary_source_dir.name}")
        
        # If we got icons from fallback directories, try to get more from fallback sources
        if len(icons) < max_files and 'fallback_dirs' in config:
            for fallback_dir in config.get('fallback_dirs', []):
                if fallback_dir.exists() and len(icons) < max_files:
                    additional_icons = scan_directory_for_png(fallback_dir, max_files=max_files - len(icons), recursive=True)
                    # Add unique icons
                    existing_names = {icon.lower() for icon in icons}
                    for icon in additional_icons:
                        if icon.lower() not in existing_names:
                            icons.append(icon)
                    if len(icons) >= max_files:
                        break
    
    copied_count = 0
    not_found = []
    
    # Search in all possible directories for each icon
    all_search_dirs = [primary_source_dir]
    if 'fallback_dirs' in config:
        all_search_dirs.extend([d for d in config['fallback_dirs'] if d.exists()])
    
    for icon_name in icons:
        source_file = None
        # Try to find the icon in any of the search directories
        for search_dir in all_search_dirs:
            found_file = find_file_recursive(search_dir, icon_name)
            if found_file and found_file.exists():
                source_file = found_file
                break
        
        if not source_file or not source_file.exists():
            not_found.append(icon_name)
            continue
        
        target_file = target_dir / icon_name
        
        try:
            shutil.copy2(source_file, target_file)
            copied_count += 1
            print(f"   [OK] Copied: {icon_name}")
        except Exception as e:
            print(f"   [ERROR] Failed to copy {icon_name}: {e}")
    
    if not_found:
        print(f"   [WARNING] Not found ({len(not_found)}): {', '.join(not_found[:5])}")
        if len(not_found) > 5:
            print(f"      ... and {len(not_found) - 5} more")
    
    return copied_count


def copy_default_images():
    """Copy default logo/images if they exist"""
    default_logo_source = Path(r'C:\Users\f_ald\OneDrive\SimpleInfoapps\LogoGFx\SimpleInfoApps.png')
    if default_logo_source.exists():
        STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        target = STATIC_IMAGES_DIR / 'SimpleInfoApps.png'
        shutil.copy2(default_logo_source, target)
        print(f"[OK] Copied default logo: SimpleInfoApps.png")
        return True
    return False


def main():
    """Main function to copy all industry icons"""
    print("=" * 60)
    print("Copying Industry Icons to Application")
    print("=" * 60)
    print()
    
    # Copy default images first
    print("1. Copying default images...")
    copy_default_images()
    print()
    
    # Copy industry icons
    total_copied = 0
    for industry, config in INDUSTRY_ICON_SOURCES.items():
        print(f"2. Copying {industry.replace('_', ' ').title()} icons...")
        copied = copy_icons(industry, config)
        total_copied += copied
        print(f"   => Copied {copied} icons\n")
    
    print("=" * 60)
    print(f"[SUCCESS] Complete! Copied {total_copied} icons total")
    print("=" * 60)
    print()
    print(f"Icons are now in: {STATIC_ICONS_DIR}")
    print("You can now update branding_service.py to use local paths.")


if __name__ == '__main__':
    main()
