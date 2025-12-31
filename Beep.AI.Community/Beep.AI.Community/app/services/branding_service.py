"""
Branding Service - White-label branding and industry-specific themes
"""
import json
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BrandingConfig:
    """
    Branding configuration for white-label customization
    Matches C# BrandingConfig structure from IdentityServer
    """
    # Application Identity
    app_name: str = "KOC A.I. Digital Campus"
    app_short_name: str = "KOC Digital Campus"
    tagline: str = "Knowledge Reservoir - Explore, Learn, Excel"
    copyright: str = "© 2025 Kuwait Oil Company. All rights reserved."
    version: str = "1.0.0"
    company_name: str = "Kuwait Oil Company"  # Legacy field for backward compatibility
    
    # Logos and Images
    logo_url: str = "/static/assets/images/SimpleInfoApps.png"
    logo_dark_url: str = "/static/assets/images/SimpleInfoApps.png"
    icon_url: str = "/static/assets/images/SimpleInfoApps.ico"
    favicon_url: str = "/static/assets/images/SimpleInfoApps.ico"
    app_icon_url: Optional[str] = None
    
    # Colors - Primary
    primary_color: str = "#4a90e2"
    primary_hover_color: str = "#3a80d2"
    primary_transparent_color: str = "rgba(74, 144, 226, 0.1)"
    primary_color_dark: str = "#6ba0f2"
    secondary_color: str = "#7b68ee"
    secondary_color_dark: str = "#9b88fe"
    tertiary_color: str = "#50c878"
    
    # Colors - Background
    background_color: str = "#ffffff"
    background_dark_color: str = "#121212"
    background_color_dark: str = "#121212"
    surface_color: str = "#F5F5F5"
    surface_elevated_color: str = "#FAFAFA"
    surface_color_dark: str = "#1E1E1E"
    border_color: str = "#E0E0E0"
    border_color_dark: str = "#424242"
    gradient_start: str = "#4a90e2"
    gradient_end: str = "#2a60c2"
    
    # Colors - Text
    text_primary_color: str = "#212121"
    text_primary_dark: str = "#FFFFFF"
    text_primary: str = "#212121"  # Alias for compatibility
    text_secondary_color: str = "#757575"
    text_secondary_dark: str = "#B0BEC5"
    text_secondary: str = "#757575"  # Alias for compatibility
    text_on_primary_color: str = "#FFFFFF"
    text_on_primary: str = "#FFFFFF"  # Alias for compatibility
    title_color: str = "#4a90e2"
    subtitle_color: str = "#424242"
    text_color: str = "#333333"  # Legacy field
    
    # Colors - Status
    success_color: str = "#50c878"
    warning_color: str = "#ffa500"
    error_color: str = "#e74c3c"
    info_color: str = "#3498db"
    
    # Typography
    font_family: str = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    heading_font_family: str = "'Inter', 'Segoe UI', system-ui, sans-serif"
    font_mono_family: str = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
    base_font_size: str = "14px"
    rtl_font_family: Optional[str] = None
    rtl_heading_font_family: Optional[str] = None
    support_rtl: bool = True
    
    # Border Radius
    border_radius: str = "8px"
    border_radius_sm: str = "6px"
    border_radius_md: str = "8px"
    border_radius_lg: str = "12px"
    border_radius_xl: str = "16px"
    
    # Login/Auth Specific
    login_background_url: str = ""
    login_background_image: Optional[str] = None
    login_title: str = "Welcome Back"
    login_welcome_message: str = "Welcome Back!"
    login_subtitle: str = "Sign in to your account"
    register_title: str = "Create Account"
    register_subtitle: str = "Get started with your new account"
    
    # Feature Flags
    is_dark_mode_default: bool = False
    default_dark_mode: bool = False  # Alias for compatibility
    enable_dark_mode: bool = True
    allow_theme_switching: bool = True
    show_version_in_footer: bool = True
    show_social_logins: bool = True
    show_remember_me: bool = True
    
    # SaaS Design System Properties
    shadow_sm: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    shadow_md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    shadow_lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    shadow_xl: str = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
    transition_duration: str = "200ms"
    transition_easing: str = "ease-out"
    
    # Gray Scale
    gray50: str = "#FAFAFA"
    gray100: str = "#F5F5F5"
    gray200: str = "#E5E5E5"
    gray300: str = "#D4D4D4"
    gray400: str = "#A3A3A3"
    gray500: str = "#737373"
    gray600: str = "#525252"
    gray700: str = "#404040"
    gray800: str = "#262626"
    gray900: str = "#171717"
    
    # Social/Contact Links
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    discord_url: Optional[str] = None
    youtube_url: Optional[str] = None
    support_email: str = "support@thetechidea.com"
    support_url: str = "/help"
    website_url: str = ""
    show_powered_by: bool = True  # Legacy field
    
    # Legacy fields for backward compatibility
    industry: str = "general"
    theme_name: str = "default"
    header_background: str = "#4a90e2"  # Legacy - use primary_color
    header_text: str = "#ffffff"  # Legacy - use text_on_primary_color
    accent_color: str = "#50c878"  # Legacy - use tertiary_color
    copyright_text: str = "© 2025 TheTechIdea. All rights reserved."  # Legacy - use copyright
    
    def synchronize_properties(self):
        """
        Synchronize alternative property names to ensure consistency.
        Call this after loading from JSON or configuration.
        """
        # Sync text color properties
        if not self.text_primary and self.text_primary_color:
            self.text_primary = self.text_primary_color
        if not self.text_primary_color and self.text_primary:
            self.text_primary_color = self.text_primary
        
        if not self.text_secondary and self.text_secondary_color:
            self.text_secondary = self.text_secondary_color
        if not self.text_secondary_color and self.text_secondary:
            self.text_secondary_color = self.text_secondary
        
        if not self.text_on_primary and self.text_on_primary_color:
            self.text_on_primary = self.text_on_primary_color
        if not self.text_on_primary_color and self.text_on_primary:
            self.text_on_primary_color = self.text_on_primary
        
        # Sync dark mode properties
        if not self.default_dark_mode and self.is_dark_mode_default:
            self.default_dark_mode = True
        if not self.is_dark_mode_default and self.default_dark_mode:
            self.is_dark_mode_default = True
        
        # Sync background properties
        if not self.background_color_dark and self.background_dark_color:
            self.background_color_dark = self.background_dark_color
        if not self.background_dark_color and self.background_color_dark:
            self.background_dark_color = self.background_color_dark
        
        # Sync login background
        if not self.login_background_url and self.login_background_image:
            self.login_background_url = self.login_background_image or ""
        if not self.login_background_image and self.login_background_url:
            self.login_background_image = self.login_background_url
        
        # Sync legacy fields
        if not self.copyright_text and self.copyright:
            self.copyright_text = self.copyright
        if not self.copyright and self.copyright_text:
            self.copyright = self.copyright_text
        
        if not self.accent_color and self.tertiary_color:
            self.accent_color = self.tertiary_color
        if not self.tertiary_color and self.accent_color:
            self.tertiary_color = self.accent_color
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BrandingConfig':
        """Create from dictionary"""
        instance = cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
        instance.synchronize_properties()
        return instance


class BrandingService:
    """Service for managing branding and white-label customization"""
    
    INDUSTRY_THEMES = {
        'oil_gas': {
            'industry': 'oil_gas',
            'company_name': 'Oil & Gas ML Platform',
            'app_name': 'Oil & Gas ML Community',
            'primary_color': '#d4af37',
            'secondary_color': '#8b4513',
            'accent_color': '#2c5aa0',
            'background_color': '#f5f5f5',
            'tagline': 'ML Solutions for Oil & Gas Industry',
            'logo_url': '/static/assets/icons/007-refinery.png',
            'theme_name': 'oil_gas'
        },
        'finance': {
            'industry': 'finance',
            'company_name': 'Financial ML Platform',
            'app_name': 'Finance ML Community',
            'primary_color': '#1e8449',
            'secondary_color': '#154360',
            'accent_color': '#d4af37',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Financial Services',
            'logo_url': '/static/assets/images/SimpleInfoApps.png',
            'theme_name': 'finance'
        },
        'healthcare': {
            'industry': 'healthcare',
            'company_name': 'Healthcare ML Platform',
            'app_name': 'Healthcare ML Community',
            'primary_color': '#0066cc',
            'secondary_color': '#00a86b',
            'accent_color': '#ff6b6b',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Healthcare & Medical Research',
            'logo_url': '/static/assets/icons/branding/healthcare.png',
            'theme_name': 'healthcare'
        },
        'real_estate': {
            'industry': 'real_estate',
            'company_name': 'Real Estate ML Platform',
            'app_name': 'Real Estate ML Community',
            'primary_color': '#8b4513',
            'secondary_color': '#daa520',
            'accent_color': '#4169e1',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Real Estate & Property Management',
            'logo_url': '/static/assets/icons/branding/real-estate.png',
            'theme_name': 'real_estate'
        },
        'retail': {
            'industry': 'retail',
            'company_name': 'Retail & E-Commerce ML Platform',
            'app_name': 'Retail ML Community',
            'primary_color': '#FF6B35',
            'secondary_color': '#C41E3A',
            'accent_color': '#2E86AB',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Retail & E-Commerce',
            'logo_url': '/static/assets/icons/retail/001-purchase.png',
            'theme_name': 'retail'
        },
        'manufacturing': {
            'industry': 'manufacturing',
            'company_name': 'Manufacturing ML Platform',
            'app_name': 'Manufacturing ML Community',
            'primary_color': '#4A5568',
            'secondary_color': '#3182CE',
            'accent_color': '#F56565',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Smart Manufacturing & Industry 4.0',
            'logo_url': '/static/assets/icons/manufacturing/002-gear.png',
            'theme_name': 'manufacturing'
        },
        'education': {
            'industry': 'education',
            'company_name': 'Education ML Platform',
            'app_name': 'Education ML Community',
            'primary_color': '#2563EB',
            'secondary_color': '#059669',
            'accent_color': '#7C3AED',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Education & Learning Analytics',
            'logo_url': '/static/assets/icons/education/008-folder.png',
            'theme_name': 'education'
        },
        'agriculture': {
            'industry': 'agriculture',
            'company_name': 'Agriculture ML Platform',
            'app_name': 'Agriculture ML Community',
            'primary_color': '#48BB78',
            'secondary_color': '#744210',
            'accent_color': '#F6E05E',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Precision Agriculture & Smart Farming',
            'logo_url': '/static/assets/icons/agriculture/002-tractor.png',
            'theme_name': 'agriculture'
        },
        'transportation': {
            'industry': 'transportation',
            'company_name': 'Transportation & Logistics ML Platform',
            'app_name': 'Transportation ML Community',
            'primary_color': '#2563EB',
            'secondary_color': '#059669',
            'accent_color': '#EA580C',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Transportation & Logistics',
            'logo_url': '/static/assets/icons/transportation/011-delivery.png',
            'theme_name': 'transportation'
        },
        'energy': {
            'industry': 'energy',
            'company_name': 'Energy & Utilities ML Platform',
            'app_name': 'Energy ML Community',
            'primary_color': '#FCD34D',
            'secondary_color': '#10B981',
            'accent_color': '#3B82F6',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Energy & Utilities Management',
            'logo_url': '/static/assets/icons/energy/005-battery.png',
            'theme_name': 'energy'
        },
        'insurance': {
            'industry': 'insurance',
            'company_name': 'Insurance ML Platform',
            'app_name': 'Insurance ML Community',
            'primary_color': '#1E3A8A',
            'secondary_color': '#047857',
            'accent_color': '#DC2626',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Insurance & Risk Management',
            'logo_url': '/static/assets/icons/insurance/016-lifebuoy.png',
            'theme_name': 'insurance'
        },
        'telecom': {
            'industry': 'telecom',
            'company_name': 'Telecommunications ML Platform',
            'app_name': 'Telecom ML Community',
            'primary_color': '#1E40AF',
            'secondary_color': '#7C3AED',
            'accent_color': '#059669',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Telecommunications',
            'logo_url': '/static/assets/icons/telecom/009-internet.png',
            'theme_name': 'telecom'
        },
        'media': {
            'industry': 'media',
            'company_name': 'Media & Entertainment ML Platform',
            'app_name': 'Media ML Community',
            'primary_color': '#9333EA',
            'secondary_color': '#EC4899',
            'accent_color': '#F97316',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Media & Entertainment',
            'logo_url': '/static/assets/icons/media/019-envelope.png',
            'theme_name': 'media'
        },
        'government': {
            'industry': 'government',
            'company_name': 'Government ML Platform',
            'app_name': 'Government ML Community',
            'primary_color': '#1E40AF',
            'secondary_color': '#DC2626',
            'accent_color': '#4B5563',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Government & Public Services',
            'logo_url': '/static/assets/icons/government/014-clipboard.png',
            'theme_name': 'government'
        },
        'sports': {
            'industry': 'sports',
            'company_name': 'Sports Analytics ML Platform',
            'app_name': 'Sports ML Community',
            'primary_color': '#EF4444',
            'secondary_color': '#10B981',
            'accent_color': '#F59E0B',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Sports Analytics & Performance',
            'logo_url': '/static/assets/icons/sports/006-target.png',
            'theme_name': 'sports'
        },
        'food_beverage': {
            'industry': 'food_beverage',
            'company_name': 'Food & Beverage ML Platform',
            'app_name': 'Food & Beverage ML Community',
            'primary_color': '#EF4444',
            'secondary_color': '#10B981',
            'accent_color': '#F59E0B',
            'background_color': '#ffffff',
            'tagline': 'ML Solutions for Food & Beverage Industry',
            'logo_url': '/static/assets/icons/food_beverage/003-calendar.png',
            'theme_name': 'food_beverage'
        },
        'general': {
            'industry': 'general',
            'company_name': 'Kuwait Oil Company',
            'app_name': 'KOC A.I. Digital Campus',
            'primary_color': '#4a90e2',
            'secondary_color': '#7b68ee',
            'accent_color': '#50c878',
            'background_color': '#ffffff',
            'tagline': 'Knowledge Reservoir - Explore, Learn, Excel',
            'logo_url': '/static/assets/images/SimpleInfoApps.png',
            'theme_name': 'default'
        }
    }
    
    @staticmethod
    def get_branding_config() -> BrandingConfig:
        """Get current branding configuration"""
        config_file = Path('instance') / 'branding.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return BrandingConfig.from_dict(data)
            except Exception:
                pass
        
        return BrandingConfig()
    
    @staticmethod
    def save_branding_config(config: BrandingConfig):
        """Save branding configuration"""
        config_file = Path('instance') / 'branding.json'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
    
    @staticmethod
    def get_industry_theme(industry: str) -> Dict:
        """Get industry-specific theme preset"""
        return BrandingService.INDUSTRY_THEMES.get(industry, BrandingService.INDUSTRY_THEMES['general'])
    
    @staticmethod
    def setup_industry_branding(industry: str, company_name: str = None, logo_path: str = None, icon_name: str = None) -> BrandingConfig:
        """Setup branding for specific industry"""
        theme = BrandingService.get_industry_theme(industry)
        
        config = BrandingConfig.from_dict(theme)
        config.industry = industry
        
        if company_name:
            config.company_name = company_name
            config.app_short_name = company_name  # Show just company name in navbar
            config.app_name = f"{company_name} ML Community"  # Full name for titles
        
        # Handle custom logo upload
        if logo_path:
            dest_dir = Path('static/assets/images/branding')
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            source = Path(logo_path)
            if source.exists():
                # Resolve paths for proper comparison
                dest_dir_resolved = dest_dir.resolve()
                source_resolved = source.resolve()
                
                # Check if file is already in the branding directory using resolved paths
                try:
                    # Check if source is within the branding directory
                    source_relative_to_dest = source_resolved.relative_to(dest_dir_resolved)
                    # File is already in branding directory, use it directly
                    config.logo_url = f"/static/assets/images/branding/{source.name}"
                except ValueError:
                    # File is not in branding directory, copy it
                    # Copy file to branding directory
                    dest = dest_dir / source.name
                    shutil.copy2(source, dest)
                    config.logo_url = f"/static/assets/images/branding/{dest.name}"
                
                config.icon_url = config.logo_url
                config.favicon_url = config.logo_url
        
        # Copy industry icons first
        copied_icons = BrandingService._copy_industry_icons(industry)
        
        # If specific icon is selected, use it as logo
        if icon_name and not logo_path:
            source_dirs = BrandingService._get_icon_source_directories()
            icon_path = BrandingService._find_icon_in_directories(icon_name, source_dirs)
            
            if icon_path:
                # Copy to branding directory
                branding_dir = Path('static/assets/icons/branding')
                branding_dir.mkdir(parents=True, exist_ok=True)
                dest = branding_dir / icon_name
                shutil.copy2(icon_path, dest)
                
                config.logo_url = f"/static/assets/icons/branding/{icon_name}"
                config.icon_url = config.logo_url
                config.favicon_url = config.logo_url
            else:
                # Try to use from already copied icons
                branding_icon = Path('static/assets/icons/branding') / icon_name
                if branding_icon.exists():
                    config.logo_url = f"/static/assets/icons/branding/{icon_name}"
                    config.icon_url = config.logo_url
                    config.favicon_url = config.logo_url
        
        config.synchronize_properties()
        BrandingService.save_branding_config(config)
        
        # Send branding to Identity Server if enabled
        BrandingService._send_branding_to_identity_server(config)
        
        return config
    
    @staticmethod
    def sync_branding_to_identity_server(config: BrandingConfig):
        """
        Sync branding configuration to Identity Server if enabled (public method)
        
        Args:
            config: BrandingConfig instance to send
        """
        BrandingService._send_branding_to_identity_server(config)
    
    @staticmethod
    def _send_branding_to_identity_server(config: BrandingConfig):
        """
        Send branding configuration to Identity Server if enabled (internal method)
        
        Args:
            config: BrandingConfig instance to send
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if Identity Server is enabled
        auth_mode = os.getenv('AUTH_MODE', 'local').lower()
        if auth_mode != 'identity_server':
            return
        
        identity_server_url = os.getenv('IDENTITY_SERVER_URL')
        if not identity_server_url:
            logger.debug("Identity Server URL not configured, skipping branding transmission")
            return
        
        try:
            from app.clients.identity_server_client import IdentityServerClient
            
            client = IdentityServerClient(
                base_url=identity_server_url,
                client_id=os.getenv('IDENTITY_SERVER_CLIENT_ID', ''),
                client_secret=os.getenv('IDENTITY_SERVER_CLIENT_SECRET', '')
            )
            
            # Map Python BrandingConfig to C# BrandingConfig structure
            branding_dict = BrandingService._map_to_csharp_branding_config(config)
            
            # Try to send branding
            success, message = client.send_branding_config(branding_dict)
            if success:
                logger.info(f"Branding configuration sent to Identity Server: {message}")
            else:
                logger.warning(f"Failed to send branding to Identity Server: {message}")
        except ImportError:
            logger.warning("Identity Server client not available, skipping branding transmission")
        except Exception as e:
            logger.error(f"Error sending branding to Identity Server: {e}", exc_info=True)
            # Don't fail setup if branding transmission fails
    
    @staticmethod
    def _map_to_csharp_branding_config(config: BrandingConfig) -> Dict:
        """
        Map Python BrandingConfig to C# BrandingConfig structure
        
        Args:
            config: Python BrandingConfig instance
            
        Returns:
            Dictionary matching C# BrandingConfig structure (PascalCase property names)
        """
        # Ensure properties are synchronized
        config.synchronize_properties()
        
        return {
            # Application Identity
            'AppName': config.app_name,
            'AppShortName': config.app_short_name,
            'Tagline': config.tagline,
            'Copyright': config.copyright or config.copyright_text,
            'Version': config.version,
            
            # Logos and Images
            'LogoUrl': config.logo_url,
            'LogoDarkUrl': config.logo_dark_url,
            'IconUrl': config.icon_url,
            'FaviconUrl': config.favicon_url,
            'AppIconUrl': config.app_icon_url,
            
            # Primary Colors
            'PrimaryColor': config.primary_color,
            'PrimaryHoverColor': config.primary_hover_color or config.primary_color,
            'PrimaryTransparentColor': config.primary_transparent_color or f"rgba({BrandingService._hex_to_rgb(config.primary_color)}, 0.1)",
            'PrimaryColorDark': config.primary_color_dark or config.primary_color,
            'SecondaryColor': config.secondary_color,
            'SecondaryColorDark': config.secondary_color_dark or config.secondary_color,
            'TertiaryColor': config.tertiary_color or config.accent_color,
            
            # Background Colors
            'BackgroundColor': config.background_color,
            'BackgroundDarkColor': config.background_dark_color or config.background_color_dark,
            'BackgroundColorDark': config.background_color_dark or config.background_dark_color,
            'SurfaceColor': config.surface_color or config.background_color,
            'SurfaceElevatedColor': config.surface_elevated_color or config.surface_color or config.background_color,
            'SurfaceColorDark': config.surface_color_dark,
            'BorderColor': config.border_color,
            'BorderColorDark': config.border_color_dark,
            'GradientStart': config.gradient_start or config.primary_color,
            'GradientEnd': config.gradient_end,
            
            # Text Colors
            'TextPrimaryColor': config.text_primary_color or config.text_color,
            'TextPrimaryDark': config.text_primary_dark,
            'TextPrimary': config.text_primary or config.text_primary_color or config.text_color,
            'TextSecondaryColor': config.text_secondary_color,
            'TextSecondaryDark': config.text_secondary_dark,
            'TextSecondary': config.text_secondary or config.text_secondary_color,
            'TextOnPrimaryColor': config.text_on_primary_color,
            'TextOnPrimary': config.text_on_primary or config.text_on_primary_color,
            'TitleColor': config.title_color or config.primary_color,
            'SubtitleColor': config.subtitle_color,
            
            # Status Colors
            'SuccessColor': config.success_color,
            'WarningColor': config.warning_color,
            'ErrorColor': config.error_color,
            'InfoColor': config.info_color,
            
            # Typography
            'FontFamily': config.font_family,
            'HeadingFontFamily': config.heading_font_family,
            'FontMonoFamily': config.font_mono_family,
            'BaseFontSize': config.base_font_size,
            'RtlFontFamily': config.rtl_font_family,
            'RtlHeadingFontFamily': config.rtl_heading_font_family,
            'SupportRtl': config.support_rtl,
            
            # Border Radius
            'BorderRadius': config.border_radius,
            'BorderRadiusSm': config.border_radius_sm,
            'BorderRadiusMd': config.border_radius_md,
            'BorderRadiusLg': config.border_radius_lg,
            'BorderRadiusXl': config.border_radius_xl,
            
            # Login/Auth Specific
            'LoginBackgroundUrl': config.login_background_url or (config.login_background_image or ""),
            'LoginBackgroundImage': config.login_background_image or config.login_background_url,
            'LoginTitle': config.login_title,
            'LoginWelcomeMessage': config.login_welcome_message or f"Welcome to {config.app_name}",
            'LoginSubtitle': config.login_subtitle or config.tagline,
            'RegisterTitle': config.register_title,
            'RegisterSubtitle': config.register_subtitle,
            
            # Feature Flags
            'IsDarkModeDefault': config.is_dark_mode_default or config.default_dark_mode,
            'DefaultDarkMode': config.default_dark_mode or config.is_dark_mode_default,
            'EnableDarkMode': config.enable_dark_mode,
            'AllowThemeSwitching': config.allow_theme_switching,
            'ShowVersionInFooter': config.show_version_in_footer,
            'ShowSocialLogins': config.show_social_logins,
            'ShowRememberMe': config.show_remember_me,
            
            # SaaS Design System Properties
            'ShadowSm': config.shadow_sm,
            'ShadowMd': config.shadow_md,
            'ShadowLg': config.shadow_lg,
            'ShadowXl': config.shadow_xl,
            'TransitionDuration': config.transition_duration,
            'TransitionEasing': config.transition_easing,
            
            # Gray Scale
            'Gray50': config.gray50,
            'Gray100': config.gray100,
            'Gray200': config.gray200,
            'Gray300': config.gray300,
            'Gray400': config.gray400,
            'Gray500': config.gray500,
            'Gray600': config.gray600,
            'Gray700': config.gray700,
            'Gray800': config.gray800,
            'Gray900': config.gray900,
            
            # Social/Contact Links
            'GitHubUrl': config.github_url,
            'TwitterUrl': config.twitter_url,
            'LinkedInUrl': config.linkedin_url,
            'DiscordUrl': config.discord_url,
            'YouTubeUrl': config.youtube_url,
            'SupportEmail': config.support_email,
            'SupportUrl': config.support_url,
            'WebsiteUrl': config.website_url
        }
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convert hex color to RGB string"""
        if not hex_color.startswith('#'):
            return '0, 0, 0'
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except:
            return '0, 0, 0'
    
    @staticmethod
    def _get_icon_source_directories() -> List[Path]:
        """Get potential icon source directories (prioritize local app icons)"""
        possible_dirs = [
            # Local app icons (primary source - copied during setup)
            Path('static/assets/icons/oil_gas'),
            Path('static/assets/icons/finance'),
            Path('static/assets/icons/healthcare'),
            Path('static/assets/icons/real_estate'),
            Path('static/assets/icons/retail'),
            Path('static/assets/icons/manufacturing'),
            Path('static/assets/icons/education'),
            Path('static/assets/icons/agriculture'),
            Path('static/assets/icons/transportation'),
            Path('static/assets/icons/energy'),
            Path('static/assets/icons/insurance'),
            Path('static/assets/icons/telecom'),
            Path('static/assets/icons/media'),
            Path('static/assets/icons/government'),
            Path('static/assets/icons/sports'),
            Path('static/assets/icons/food_beverage'),
            Path('static/assets/icons/general'),
            Path('static/assets/icons'),
            Path('static/assets/images'),
            # External icon pack directories (fallback for development/setup)
            # Prioritize H:\dev\iconPacks\imgs for recursive search
            Path(r'H:\dev\iconPacks\imgs'),
            Path(r'H:\dev\iconPacks\oilandgas32mycollection\png'),
            Path(r'H:\dev\iconPacks\BusinessandFinance'),
            Path(r'H:\dev\iconPacks\healthcare'),
            Path(r'H:\dev\iconPacks\real-estate'),
            Path(r'H:\dev\iconPacks\files-formats'),
            # Alternative locations
            Path('assets/icons'),
            Path('icons'),
        ]
        
        # Filter to only existing directories
        return [d for d in possible_dirs if d.exists()]
    
    @staticmethod
    def _find_icon_in_directories(icon_name: str, source_dirs: List[Path]) -> Optional[Path]:
        """
        Find an icon file in the given directories (recursively searches H:\dev\iconPacks\imgs)
        Also searches in subdirectories for all directories
        """
        for source_dir in source_dirs:
            # Check direct path first
            icon_path = source_dir / icon_name
            if icon_path.exists() and icon_path.is_file():
                return icon_path
            
            # Try recursive search for all directories (especially H:\dev\iconPacks\imgs)
            try:
                # Recursively search for the icon file in subdirectories
                for found_path in source_dir.rglob(icon_name):
                    if found_path.is_file():
                        return found_path
            except Exception:
                # If recursive search fails, continue to next directory
                continue
        
        return None
    
    @staticmethod
    def _scan_directory_for_png_files(directory: Path, max_files: int = 20) -> List[str]:
        """Scan a directory for PNG files and return list of filenames"""
        png_files = []
        if directory.exists():
            try:
                for file_path in directory.glob('*.png'):
                    if len(png_files) >= max_files:
                        break
                    png_files.append(file_path.name)
            except Exception:
                pass
        return png_files[:max_files]
    
    @staticmethod
    def get_available_icons_for_industry(industry: str) -> List[Dict]:
        """Get list of available icons for a specific industry"""
        icon_map = {
            'oil_gas': [
                '007-refinery.png',
                '002-tanker.png',
                '003-oil-tank.png',
                '004-oil-tank-1.png',
                '005-storage-tank.png',
                '011-oil-industry.png',
                '057-oil-platform.png',
                '063-oil-rig.png',
                '066-oil-platform-1.png',
                '067-oil-rig-1.png',
                '069-oil-rig-3.png'
            ],
        'finance': [
            '001-financial crisis.png',
            '002-depression.png',
            '003-recession.png',
            '004-economic growth.png',
            '005-fund.png',
            '006-devaluation.png',
            '007-conflict.png',
            '008-economic growth.png',
            '009-inflation.png',
            '010-global crisis.png',
            '011-processing.png',
            '012-deficit.png',
            '013-credit.png',
            '014-consumer.png',
            '015-crisis.png'
        ],
        'healthcare': [
            '001-dumbbell.png',
            '002-gym.png',
            '003-runner.png',
            '004-volleyball.png',
            '005-tennis racket.png',
            '006-temperature.png',
            '007-tooth.png',
            '008-swimming pool.png',
            '009-stopwatch.png',
            '010-stethoscope.png',
            '011-sleep.png',
            '012-shower head.png',
            '013-sneaker.png',
            '014-tshirt.png',
            '015-salad.png'
        ],
        'real_estate': [
            '001-for sale.png',
            '002-mail.png',
            '003-analytics.png',
            '004-location.png',
            '005-shopping.png',
            '006-Helpline.png',
            '007-advertising.png',
            '008-discount.png',
            '009-balance.png',
            '010-new house.png',
            '011-offering.png',
            '012-home network.png',
            '013-deal.png',
            '014-price tag.png',
            '015-property.png'
        ],
        'retail': [
            '001-purchase.png',
            '002-shop bag.png',
            '003-truck.png',
            '004-online store.png',
            '005-payment.png',
            '006-invoice.png',
            '007-groceries.png',
            '008-gift.png',
            '009-vending machine.png',
            '010-discount.png',
            '011-shopping cart.png',
            '012-shelf.png',
            '013-cash register.png',
            '014-wallet.png',
            '015-person.png'
        ],
        'manufacturing': [
            '001-earth.png',
            '002-gear.png',
            '003-calendar.png',
            '017-chart.png',
            '018-graph.png',
            '014-clipboard.png',
            '015-documents.png'
        ],
        'education': [
            '008-folder.png',
            '014-clipboard.png',
            '015-documents.png',
            '003-calendar.png',
            '006-target.png'
        ],
        'agriculture': [
            '001-rubber gloves.png',
            '002-tractor.png',
            '003-carrot.png',
            '004-barrier.png',
            '005-forecast.png',
            '006-temperature.png',
            '007-well.png',
            '008-bird house.png',
            '011-wheelbarrow.png',
            '015-growing plant.png'
        ],
        'transportation': [
            '001-air-freight.png',
            '002-airship.png',
            '007-cargo-ship.png',
            '008-cargo-train.png',
            '011-delivery.png',
            '012-crane.png',
            '013-container-crane.png',
            '014-conveyor.png',
            '016-delivered.png',
            '018-delivery-man.png'
        ],
        'energy': [
            '001-accumulator.png',
            '002-air cooler.png',
            '005-battery.png',
            '012-charging battery.png',
            '013-charging station.png',
            '015-eco fuel.png',
            '016-ecology.png',
            '019-energy sources.png',
            '020-electric car.png'
        ],
        'insurance': [
            '001-claim.png',
            '002-health insurance.png',
            '003-building.png',
            '004-agent.png',
            '005-car.png',
            '009-family.png',
            '010-money.png',
            '016-lifebuoy.png',
            '017-fire.png',
            '019-law.png'
        ],
        'telecom': [
            '001-earth.png',
            '007-cloud.png',
            '009-internet.png',
            '019-envelope.png',
            '020-phone.png'
        ],
        'media': [
            '019-envelope.png',
            '020-phone.png',
            '007-cloud.png',
            '009-internet.png'
        ],
        'government': [
            '014-clipboard.png',
            '015-documents.png',
            '003-calendar.png',
            '001-earth.png'
        ],
        'sports': [
            '006-target.png',
            '003-calendar.png',
            '017-chart.png',
            '018-graph.png'
        ],
        'food_beverage': [
            '003-calendar.png',
            '011-sun.png',
            '017-chart.png',
            '018-graph.png'
        ],
        'general': [
                'SimpleInfoApps.png',
                'logo.png',
                'icon.png'
            ]
        }
        
        # For healthcare and real_estate, scan directories if icon list is empty
        icons_to_find = icon_map.get(industry, [])
        source_dirs = BrandingService._get_icon_source_directories()
        available_icons = []
        
        # Auto-scan for industries if icon list is empty (fallback)
        if not icons_to_find:
            industry_dir_map = {
                'healthcare': Path('static/assets/icons/healthcare'),
                'real_estate': Path('static/assets/icons/real_estate'),
                'finance': Path('static/assets/icons/finance'),
                'retail': Path('static/assets/icons/retail'),
                'manufacturing': Path('static/assets/icons/manufacturing'),
                'education': Path('static/assets/icons/education'),
                'agriculture': Path('static/assets/icons/agriculture'),
                'transportation': Path('static/assets/icons/transportation'),
                'energy': Path('static/assets/icons/energy'),
                'insurance': Path('static/assets/icons/insurance'),
                'telecom': Path('static/assets/icons/telecom'),
                'media': Path('static/assets/icons/media'),
                'government': Path('static/assets/icons/government'),
                'sports': Path('static/assets/icons/sports'),
                'food_beverage': Path('static/assets/icons/food_beverage')
            }
            scan_dir = industry_dir_map.get(industry)
            if scan_dir and scan_dir.exists():
                icons_to_find = BrandingService._scan_directory_for_png_files(scan_dir, max_files=15)
        
        # Find icons in directories
        branding_dir = Path('static/assets/icons/branding')
        branding_dir.mkdir(parents=True, exist_ok=True)
        found_icons = []
        
        for icon_name in icons_to_find:
            icon_path = BrandingService._find_icon_in_directories(icon_name, source_dirs)
            if icon_path:
                # Copy to branding directory if not already there
                dest_path = branding_dir / icon_name
                try:
                    if not dest_path.exists():
                        shutil.copy2(icon_path, dest_path)
                    found_icons.append({
                        'name': icon_name,
                        'path': str(dest_path),
                        'url': f'/static/assets/icons/branding/{icon_name}'
                    })
                except Exception as e:
                    logger.debug(f"Failed to copy icon {icon_name} to branding directory: {e}")
                    # Still add it with original path if copy fails
                    found_icons.append({
                        'name': icon_name,
                        'path': str(icon_path),
                        'url': f'/static/assets/icons/branding/{icon_name}' if 'static' in str(icon_path) else None
                    })
        
        # If we found some icons, use them (even if not all requested icons were found)
        if found_icons:
            return found_icons
        
        # Fallback: if no specific icons were found, try to find ANY icons from industry directories
        fallback_found = []
        for source_dir in source_dirs:
            try:
                # Recursively search for any PNG files
                for png_file in list(source_dir.rglob('*.png'))[:12]:  # Get first 12 icons
                    if png_file.is_file():
                        icon_name = png_file.name
                        dest_path = branding_dir / icon_name
                        try:
                            if not dest_path.exists():
                                shutil.copy2(png_file, dest_path)
                            fallback_found.append({
                                'name': icon_name,
                                'path': str(dest_path),
                                'url': f'/static/assets/icons/branding/{icon_name}'
                            })
                            if len(fallback_found) >= 12:
                                break
                        except Exception as e:
                            logger.debug(f"Failed to copy fallback icon {icon_name}: {e}")
                            continue
                if fallback_found:
                    break  # Stop after finding icons in first successful directory
            except Exception as e:
                logger.debug(f"Fallback icon search in {source_dir} failed: {e}")
                continue
        
        return fallback_found if fallback_found else []
    
    @staticmethod
    def _copy_industry_icons(industry: str):
        """Copy industry-specific icons to branding folder"""
        branding_dir = Path('static/assets/icons/branding')
        branding_dir.mkdir(parents=True, exist_ok=True)
        
        # Use the full icon_map from get_available_icons_for_industry to ensure all icons are included
        icon_map = {
            'oil_gas': [
                '007-refinery.png',
                '002-tanker.png',
                '003-oil-tank.png',
                '004-oil-tank-1.png',
                '005-storage-tank.png',
                '011-oil-industry.png',
                '057-oil-platform.png',
                '063-oil-rig.png',
                '066-oil-platform-1.png',
                '067-oil-rig-1.png',
                '069-oil-rig-3.png'
            ],
            'finance': [
                'analytics.png',
                'analytics-1.png',
                'analytics-2.png',
                'dashboard.png',
                'dashboard-1.png',
                'monitor.png',
                'predictive-chart.png'
            ],
            'healthcare': [],  # Will auto-scan and copy
            'real_estate': []  # Will auto-scan and copy
        }
        
        icons_to_copy = icon_map.get(industry, [])
        source_dirs = BrandingService._get_icon_source_directories()
        
        # Auto-scan for industries if icon list is empty (fallback)
        if not icons_to_copy:
            industry_dir_map = {
                'healthcare': Path('static/assets/icons/healthcare'),
                'real_estate': Path('static/assets/icons/real_estate'),
                'finance': Path('static/assets/icons/finance'),
                'retail': Path('static/assets/icons/retail'),
                'manufacturing': Path('static/assets/icons/manufacturing'),
                'education': Path('static/assets/icons/education'),
                'agriculture': Path('static/assets/icons/agriculture'),
                'transportation': Path('static/assets/icons/transportation'),
                'energy': Path('static/assets/icons/energy'),
                'insurance': Path('static/assets/icons/insurance'),
                'telecom': Path('static/assets/icons/telecom'),
                'media': Path('static/assets/icons/media'),
                'government': Path('static/assets/icons/government'),
                'sports': Path('static/assets/icons/sports'),
                'food_beverage': Path('static/assets/icons/food_beverage')
            }
            scan_dir = industry_dir_map.get(industry)
            if scan_dir and scan_dir.exists():
                icons_to_copy = BrandingService._scan_directory_for_png_files(scan_dir, max_files=10)
        
        copied_count = 0
        for icon_name in icons_to_copy:
            icon_path = BrandingService._find_icon_in_directories(icon_name, source_dirs)
            if icon_path:
                dest = branding_dir / icon_name
                try:
                    # Only copy if file doesn't already exist or is different
                    if not dest.exists() or dest.stat().st_size != icon_path.stat().st_size:
                        shutil.copy2(icon_path, dest)
                    copied_count += 1
                except Exception as e:
                    logger.debug(f"Failed to copy icon {icon_name}: {e}")
                    pass  # Skip if copy fails
        
        return copied_count
    
    @staticmethod
    def get_available_industries() -> List[Dict]:
        """Get list of available industry presets"""
        industries = []
        for key, theme in BrandingService.INDUSTRY_THEMES.items():
            industries.append({
                'id': key,
                'name': theme.get('company_name', key.replace('_', ' ').title()),
                'tagline': theme.get('tagline', ''),
                'primary_color': theme.get('primary_color', '#4a90e2')
            })
        return industries
    
    @staticmethod
    def generate_css_variables(config: BrandingConfig) -> str:
        """Generate CSS custom properties from branding config"""
        css = ":root {\n"
        
        css_vars = {
            '--primary-color': config.primary_color,
            '--secondary-color': config.secondary_color,
            '--accent-color': config.accent_color,
            '--background-color': config.background_color,
            '--text-color': config.text_color,
            '--header-background': config.header_background,
            '--header-text': config.header_text,
            '--success-color': config.success_color,
            '--warning-color': config.warning_color,
            '--error-color': config.error_color,
            '--info-color': config.info_color,
            '--company-name': f'"{config.company_name}"',
            '--app-name': f'"{config.app_name}"',
            '--tagline': f'"{config.tagline}"',
            '--industry': f'"{config.industry}"'
        }
        
        for var_name, value in css_vars.items():
            css += f"  {var_name}: {value};\n"
        
        css += "}\n"
        return css
    
    @staticmethod
    def is_configured() -> bool:
        """Check if branding is configured"""
        config_file = Path('instance') / 'branding.json'
        return config_file.exists()
