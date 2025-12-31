"""
Script to seed initial industry scenarios data
Run this after creating the database and running migrations
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.services.industry_scenarios_service import IndustryScenariosService

def main():
    """Seed industry scenarios"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Seeding Industry Scenarios")
        print("=" * 60)
        print()
        
        try:
            # Check if scenarios already exist
            from app.models.industry_scenario import IndustryScenario
            existing_count = IndustryScenario.query.count()
            
            if existing_count > 0:
                print(f"[INFO] Found {existing_count} existing scenarios.")
                response = input("Do you want to add new scenarios? (y/n): ")
                if response.lower() != 'y':
                    print("Seeding cancelled.")
                    return
            
            # Seed scenarios
            seeded_count = IndustryScenariosService.seed_initial_scenarios()
            
            print()
            print("=" * 60)
            print(f"[SUCCESS] Seeded {seeded_count} scenarios successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] Failed to seed scenarios: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()
