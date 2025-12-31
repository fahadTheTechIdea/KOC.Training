"""
Industries web routes
"""
from flask import Blueprint, render_template, request
from app.services.branding_service import BrandingService
from app.services.industry_scenarios_service import IndustryScenariosService

industries_bp = Blueprint('industries', __name__)


@industries_bp.route('/')
def list_industries():
    """List all available industries"""
    branding = BrandingService.get_branding_config()
    service = BrandingService()
    
    industries = service.get_available_industries()
    
    return render_template(
        'industries/list.html',
        industries=industries,
        branding=branding
    )


@industries_bp.route('/<industry>')
def industry_detail(industry):
    """Industry detail page with scenarios"""
    branding = BrandingService.get_branding_config()
    scenarios_service = IndustryScenariosService()
    
    # Get industry theme
    service = BrandingService()
    industry_theme = service.get_industry_theme(industry)
    
    if not industry_theme:
        from flask import abort
        abort(404, description="Industry not found")
    
    # Get scenarios for this industry
    use_cases = scenarios_service.get_use_cases(industry)
    dataset_ideas = scenarios_service.get_dataset_ideas(industry)
    competition_ideas = scenarios_service.get_competition_ideas(industry)
    
    # Get available icons
    available_icons = service.get_available_icons_for_industry(industry)
    
    return render_template(
        'industries/detail.html',
        industry=industry,
        industry_theme=industry_theme,
        use_cases=use_cases,
        dataset_ideas=dataset_ideas,
        competition_ideas=competition_ideas,
        available_icons=available_icons,
        branding=branding
    )
