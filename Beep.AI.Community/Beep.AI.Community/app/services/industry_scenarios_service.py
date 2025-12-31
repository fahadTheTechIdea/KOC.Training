"""
Industry Scenarios Service - Manage scenarios (use cases, dataset ideas, competition ideas) per industry
"""
from typing import List, Dict, Optional, Tuple
from app import db
from app.models.industry_scenario import IndustryScenario
import logging

logger = logging.getLogger(__name__)


class IndustryScenariosService:
    """Service for managing industry scenarios"""
    
    @staticmethod
    def get_scenarios_for_industry(industry: str, scenario_type: Optional[str] = None) -> List[Dict]:
        """Get all scenarios for an industry, optionally filtered by type"""
        query = IndustryScenario.query.filter_by(industry=industry, is_active=True)
        
        if scenario_type:
            query = query.filter_by(scenario_type=scenario_type)
        
        scenarios = query.order_by(IndustryScenario.priority.desc(), IndustryScenario.created_at.desc()).all()
        return [scenario.to_dict() for scenario in scenarios]
    
    @staticmethod
    def get_use_cases(industry: str) -> List[Dict]:
        """Get use cases for an industry"""
        return IndustryScenariosService.get_scenarios_for_industry(industry, scenario_type='use_case')
    
    @staticmethod
    def get_dataset_ideas(industry: str) -> List[Dict]:
        """Get dataset ideas for an industry"""
        return IndustryScenariosService.get_scenarios_for_industry(industry, scenario_type='dataset_idea')
    
    @staticmethod
    def get_competition_ideas(industry: str) -> List[Dict]:
        """Get competition ideas for an industry"""
        return IndustryScenariosService.get_scenarios_for_industry(industry, scenario_type='competition_idea')
    
    @staticmethod
    def add_scenario(
        industry: str,
        scenario_type: str,
        title: str,
        description: str,
        icon_name: Optional[str] = None,
        priority: int = 0,
        details: Optional[Dict] = None
    ) -> Tuple[IndustryScenario, Optional[str]]:
        """Add a new scenario"""
        try:
            scenario = IndustryScenario(
                industry=industry,
                scenario_type=scenario_type,
                title=title,
                description=description,
                icon_name=icon_name,
                priority=priority,
                details=details or {}
            )
            
            db.session.add(scenario)
            db.session.commit()
            
            logger.info(f"Added scenario: {industry} - {scenario_type} - {title}")
            return scenario, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding scenario: {e}")
            return None, str(e)
    
    @staticmethod
    def update_scenario(
        scenario_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        icon_name: Optional[str] = None,
        priority: Optional[int] = None,
        details: Optional[Dict] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[Optional[IndustryScenario], Optional[str]]:
        """Update an existing scenario"""
        try:
            scenario = IndustryScenario.query.get(scenario_id)
            if not scenario:
                return None, "Scenario not found"
            
            if title is not None:
                scenario.title = title
            if description is not None:
                scenario.description = description
            if icon_name is not None:
                scenario.icon_name = icon_name
            if priority is not None:
                scenario.priority = priority
            if details is not None:
                scenario.details = details
            if is_active is not None:
                scenario.is_active = is_active
            
            db.session.commit()
            
            logger.info(f"Updated scenario: {scenario_id}")
            return scenario, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating scenario: {e}")
            return None, str(e)
    
    @staticmethod
    def delete_scenario(scenario_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a scenario (soft delete by setting is_active=False)"""
        try:
            scenario = IndustryScenario.query.get(scenario_id)
            if not scenario:
                return False, "Scenario not found"
            
            scenario.is_active = False
            db.session.commit()
            
            logger.info(f"Deleted scenario: {scenario_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting scenario: {e}")
            return False, str(e)
    
    @staticmethod
    def get_scenario(scenario_id: int) -> Optional[IndustryScenario]:
        """Get a single scenario by ID"""
        return IndustryScenario.query.get(scenario_id)
    
    @staticmethod
    def seed_initial_scenarios():
        """Seed initial scenarios for all industries"""
        scenarios_data = IndustryScenariosService._get_scenarios_data()
        
        seeded_count = 0
        for scenario_data in scenarios_data:
            # Check if scenario already exists
            existing = IndustryScenario.query.filter_by(
                industry=scenario_data['industry'],
                scenario_type=scenario_data['scenario_type'],
                title=scenario_data['title']
            ).first()
            
            if not existing:
                scenario, error = IndustryScenariosService.add_scenario(**scenario_data)
                if not error:
                    seeded_count += 1
                else:
                    logger.warning(f"Failed to seed scenario: {error}")
        
        logger.info(f"Seeded {seeded_count} scenarios")
        return seeded_count
    
    @staticmethod
    def _get_scenarios_data() -> List[Dict]:
        """Get initial scenarios data for all industries"""
        scenarios = []
        
        # Retail scenarios
        scenarios.extend([
            {
                'industry': 'retail',
                'scenario_type': 'use_case',
                'title': 'Customer Segmentation and Behavior Prediction',
                'description': 'Analyze customer purchase patterns to segment customers and predict future buying behavior for targeted marketing campaigns.',
                'priority': 10,
                'icon_name': '001-purchase.png'
            },
            {
                'industry': 'retail',
                'scenario_type': 'use_case',
                'title': 'Inventory Management and Supply Chain Optimization',
                'description': 'Optimize inventory levels and supply chain processes to reduce costs and improve availability.',
                'priority': 10,
                'icon_name': '003-truck.png'
            },
            {
                'industry': 'retail',
                'scenario_type': 'use_case',
                'title': 'Fraud Detection in Transactions',
                'description': 'Detect fraudulent transactions in real-time to prevent financial losses and protect customers.',
                'priority': 9,
                'icon_name': '005-payment.png'
            },
            {
                'industry': 'retail',
                'scenario_type': 'dataset_idea',
                'title': 'E-commerce Customer Transactions',
                'description': 'Historical customer transaction data including purchases, returns, and browsing behavior for analysis.',
                'priority': 10
            },
            {
                'industry': 'retail',
                'scenario_type': 'dataset_idea',
                'title': 'Inventory and Sales Data',
                'description': 'Product inventory levels, sales history, and stock movements for demand forecasting.',
                'priority': 9
            },
            {
                'industry': 'retail',
                'scenario_type': 'competition_idea',
                'title': 'Customer Lifetime Value Prediction',
                'description': 'Predict customer lifetime value based on purchase history and behavior patterns.',
                'priority': 10,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            },
            {
                'industry': 'retail',
                'scenario_type': 'competition_idea',
                'title': 'Product Recommendation Engine',
                'description': 'Build a recommendation system to suggest products to customers based on their preferences.',
                'priority': 9,
                'details': {'metric': 'Precision@K', 'submission_format': 'JSON'}
            }
        ])
        
        # Manufacturing scenarios
        scenarios.extend([
            {
                'industry': 'manufacturing',
                'scenario_type': 'use_case',
                'title': 'Predictive Maintenance for Machinery',
                'description': 'Predict equipment failures before they occur to minimize downtime and maintenance costs.',
                'priority': 10,
                'icon_name': '002-gear.png'
            },
            {
                'industry': 'manufacturing',
                'scenario_type': 'use_case',
                'title': 'Quality Control and Defect Detection',
                'description': 'Automatically detect product defects using computer vision and ML models.',
                'priority': 10,
                'icon_name': '006-target.png'
            },
            {
                'industry': 'manufacturing',
                'scenario_type': 'dataset_idea',
                'title': 'Sensor Data from Manufacturing Equipment',
                'description': 'IoT sensor data including temperature, vibration, pressure, and other metrics from production machinery.',
                'priority': 10
            },
            {
                'industry': 'manufacturing',
                'scenario_type': 'competition_idea',
                'title': 'Predictive Maintenance Challenge',
                'description': 'Predict when manufacturing equipment will fail based on sensor data.',
                'priority': 10,
                'details': {'metric': 'F1-Score', 'submission_format': 'CSV'}
            }
        ])
        
        # Education scenarios
        scenarios.extend([
            {
                'industry': 'education',
                'scenario_type': 'use_case',
                'title': 'Student Success Prediction',
                'description': 'Predict student performance and identify at-risk students early for intervention.',
                'priority': 10,
                'icon_name': '014-clipboard.png'
            },
            {
                'industry': 'education',
                'scenario_type': 'use_case',
                'title': 'Personalized Learning Paths',
                'description': 'Create adaptive learning paths tailored to individual student needs and learning styles.',
                'priority': 9,
                'icon_name': '015-documents.png'
            },
            {
                'industry': 'education',
                'scenario_type': 'dataset_idea',
                'title': 'Student Performance and Engagement Data',
                'description': 'Student grades, attendance, assignment completion, and engagement metrics.',
                'priority': 10
            },
            {
                'industry': 'education',
                'scenario_type': 'competition_idea',
                'title': 'Student Dropout Prediction',
                'description': 'Identify students at risk of dropping out based on academic and engagement data.',
                'priority': 10,
                'details': {'metric': 'AUC-ROC', 'submission_format': 'CSV'}
            }
        ])
        
        # Agriculture scenarios
        scenarios.extend([
            {
                'industry': 'agriculture',
                'scenario_type': 'use_case',
                'title': 'Crop Yield Prediction and Optimization',
                'description': 'Predict crop yields based on weather, soil conditions, and farming practices.',
                'priority': 10,
                'icon_name': '002-tractor.png'
            },
            {
                'industry': 'agriculture',
                'scenario_type': 'use_case',
                'title': 'Disease Detection in Plants',
                'description': 'Identify plant diseases early using image classification and sensor data.',
                'priority': 9,
                'icon_name': '015-growing plant.png'
            },
            {
                'industry': 'agriculture',
                'scenario_type': 'dataset_idea',
                'title': 'Agricultural Sensor and Weather Data',
                'description': 'Soil moisture, temperature, weather patterns, and crop growth data from IoT sensors.',
                'priority': 10
            },
            {
                'industry': 'agriculture',
                'scenario_type': 'competition_idea',
                'title': 'Crop Yield Forecasting',
                'description': 'Predict crop yields for the next season based on historical and environmental data.',
                'priority': 10,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            }
        ])
        
        # Transportation scenarios
        scenarios.extend([
            {
                'industry': 'transportation',
                'scenario_type': 'use_case',
                'title': 'Route Optimization and Traffic Prediction',
                'description': 'Optimize delivery routes and predict traffic conditions for efficient logistics.',
                'priority': 10,
                'icon_name': '011-delivery.png'
            },
            {
                'industry': 'transportation',
                'scenario_type': 'use_case',
                'title': 'Demand Forecasting for Ridesharing',
                'description': 'Predict rider demand to optimize driver allocation and reduce wait times.',
                'priority': 9,
                'icon_name': '018-delivery-man.png'
            },
            {
                'industry': 'transportation',
                'scenario_type': 'dataset_idea',
                'title': 'GPS and Route Data',
                'description': 'Vehicle GPS tracking, route history, traffic patterns, and delivery performance data.',
                'priority': 10
            },
            {
                'industry': 'transportation',
                'scenario_type': 'competition_idea',
                'title': 'Delivery Time Prediction',
                'description': 'Predict delivery times based on route, traffic, and historical data.',
                'priority': 9,
                'details': {'metric': 'MAE', 'submission_format': 'CSV'}
            }
        ])
        
        # Energy scenarios
        scenarios.extend([
            {
                'industry': 'energy',
                'scenario_type': 'use_case',
                'title': 'Energy Consumption Prediction',
                'description': 'Forecast energy consumption patterns to optimize grid load and reduce costs.',
                'priority': 10,
                'icon_name': '005-battery.png'
            },
            {
                'industry': 'energy',
                'scenario_type': 'use_case',
                'title': 'Renewable Energy Forecasting',
                'description': 'Predict solar and wind energy generation based on weather patterns.',
                'priority': 10,
                'icon_name': '019-energy sources.png'
            },
            {
                'industry': 'energy',
                'scenario_type': 'dataset_idea',
                'title': 'Smart Grid and Energy Consumption Data',
                'description': 'Smart meter readings, energy consumption patterns, and grid load data.',
                'priority': 10
            },
            {
                'industry': 'energy',
                'scenario_type': 'competition_idea',
                'title': 'Solar Energy Generation Prediction',
                'description': 'Predict solar panel energy output based on weather and historical data.',
                'priority': 10,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            }
        ])
        
        # Insurance scenarios
        scenarios.extend([
            {
                'industry': 'insurance',
                'scenario_type': 'use_case',
                'title': 'Risk Assessment and Pricing',
                'description': 'Assess risk levels and determine appropriate insurance premiums.',
                'priority': 10,
                'icon_name': '016-lifebuoy.png'
            },
            {
                'industry': 'insurance',
                'scenario_type': 'use_case',
                'title': 'Fraud Detection in Claims',
                'description': 'Identify potentially fraudulent insurance claims using ML models.',
                'priority': 10,
                'icon_name': '001-claim.png'
            },
            {
                'industry': 'insurance',
                'scenario_type': 'dataset_idea',
                'title': 'Insurance Claims and Policy Data',
                'description': 'Historical claims data, policy information, and customer demographics.',
                'priority': 10
            },
            {
                'industry': 'insurance',
                'scenario_type': 'competition_idea',
                'title': 'Insurance Fraud Detection',
                'description': 'Identify fraudulent insurance claims using historical data and ML techniques.',
                'priority': 10,
                'details': {'metric': 'F1-Score', 'submission_format': 'CSV'}
            }
        ])
        
        # Telecom scenarios
        scenarios.extend([
            {
                'industry': 'telecom',
                'scenario_type': 'use_case',
                'title': 'Network Performance Optimization',
                'description': 'Optimize network performance and capacity planning based on usage patterns.',
                'priority': 10,
                'icon_name': '009-internet.png'
            },
            {
                'industry': 'telecom',
                'scenario_type': 'use_case',
                'title': 'Customer Churn Prediction',
                'description': 'Predict which customers are likely to churn and take proactive retention measures.',
                'priority': 10,
                'icon_name': '020-phone.png'
            },
            {
                'industry': 'telecom',
                'scenario_type': 'dataset_idea',
                'title': 'Network Usage and Customer Data',
                'description': 'Network traffic data, customer usage patterns, service quality metrics.',
                'priority': 10
            },
            {
                'industry': 'telecom',
                'scenario_type': 'competition_idea',
                'title': 'Customer Churn Prediction Challenge',
                'description': 'Predict customer churn based on usage patterns and service history.',
                'priority': 10,
                'details': {'metric': 'AUC-ROC', 'submission_format': 'CSV'}
            }
        ])
        
        # Media scenarios
        scenarios.extend([
            {
                'industry': 'media',
                'scenario_type': 'use_case',
                'title': 'Content Recommendation Engines',
                'description': 'Recommend personalized content to users based on viewing history and preferences.',
                'priority': 10,
                'icon_name': '019-envelope.png'
            },
            {
                'industry': 'media',
                'scenario_type': 'dataset_idea',
                'title': 'Media Consumption and User Behavior',
                'description': 'User viewing history, ratings, interactions, and content metadata.',
                'priority': 10
            },
            {
                'industry': 'media',
                'scenario_type': 'competition_idea',
                'title': 'Content Recommendation System',
                'description': 'Build a recommendation system that maximizes user engagement and satisfaction.',
                'priority': 10,
                'details': {'metric': 'NDCG', 'submission_format': 'JSON'}
            }
        ])
        
        # Government scenarios
        scenarios.extend([
            {
                'industry': 'government',
                'scenario_type': 'use_case',
                'title': 'Public Policy Impact Analysis',
                'description': 'Analyze the impact of public policies using historical data and ML models.',
                'priority': 10,
                'icon_name': '014-clipboard.png'
            },
            {
                'industry': 'government',
                'scenario_type': 'use_case',
                'title': 'Citizen Service Optimization',
                'description': 'Optimize public service delivery and resource allocation.',
                'priority': 9,
                'icon_name': '015-documents.png'
            },
            {
                'industry': 'government',
                'scenario_type': 'dataset_idea',
                'title': 'Public Services and Citizen Data',
                'description': 'Anonymized public service usage data, citizen feedback, and resource allocation metrics.',
                'priority': 10
            }
        ])
        
        # Sports scenarios
        scenarios.extend([
            {
                'industry': 'sports',
                'scenario_type': 'use_case',
                'title': 'Player Performance Analysis',
                'description': 'Analyze player performance data to optimize team strategies and training.',
                'priority': 10,
                'icon_name': '006-target.png'
            },
            {
                'industry': 'sports',
                'scenario_type': 'use_case',
                'title': 'Injury Prediction and Prevention',
                'description': 'Predict injury risks based on player performance and health data.',
                'priority': 9,
                'icon_name': '017-chart.png'
            },
            {
                'industry': 'sports',
                'scenario_type': 'dataset_idea',
                'title': 'Sports Performance and Statistics',
                'description': 'Player statistics, game performance data, and health metrics.',
                'priority': 10
            },
            {
                'industry': 'sports',
                'scenario_type': 'competition_idea',
                'title': 'Player Performance Prediction',
                'description': 'Predict player performance in upcoming games based on historical data.',
                'priority': 9,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            }
        ])
        
        # Food & Beverage scenarios
        scenarios.extend([
            {
                'industry': 'food_beverage',
                'scenario_type': 'use_case',
                'title': 'Supply Chain Optimization',
                'description': 'Optimize food supply chains to reduce waste and improve efficiency.',
                'priority': 10
            },
            {
                'industry': 'food_beverage',
                'scenario_type': 'use_case',
                'title': 'Quality Control and Safety',
                'description': 'Detect food quality issues and safety hazards using ML models.',
                'priority': 10
            },
            {
                'industry': 'food_beverage',
                'scenario_type': 'dataset_idea',
                'title': 'Food Supply Chain and Quality Data',
                'description': 'Supply chain logistics data, quality control metrics, and safety inspection records.',
                'priority': 10
            }
        ])
        
        # Oil & Gas scenarios (existing industry)
        scenarios.extend([
            {
                'industry': 'oil_gas',
                'scenario_type': 'use_case',
                'title': 'Predictive Maintenance for Oil Rigs',
                'description': 'Predict equipment failures in oil rigs and pipelines to prevent costly downtime.',
                'priority': 10,
                'icon_name': '063-oil-rig.png'
            },
            {
                'industry': 'oil_gas',
                'scenario_type': 'dataset_idea',
                'title': 'Oil Well Production Data',
                'description': 'Production metrics, sensor data from oil wells, and extraction performance data.',
                'priority': 10
            }
        ])
        
        # Finance scenarios (existing industry)
        scenarios.extend([
            {
                'industry': 'finance',
                'scenario_type': 'use_case',
                'title': 'Credit Risk Assessment',
                'description': 'Assess credit risk for loan applications using ML models.',
                'priority': 10,
                'icon_name': '013-credit.png'
            },
            {
                'industry': 'finance',
                'scenario_type': 'competition_idea',
                'title': 'Stock Price Prediction',
                'description': 'Predict stock prices based on historical data and market indicators.',
                'priority': 9,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            }
        ])
        
        # Healthcare scenarios (existing industry)
        scenarios.extend([
            {
                'industry': 'healthcare',
                'scenario_type': 'use_case',
                'title': 'Medical Diagnosis Assistance',
                'description': 'Assist healthcare professionals with diagnosis using medical imaging and patient data.',
                'priority': 10,
                'icon_name': '010-stethoscope.png'
            },
            {
                'industry': 'healthcare',
                'scenario_type': 'dataset_idea',
                'title': 'Medical Imaging and Patient Data',
                'description': 'Medical images, patient records, and diagnostic data (properly anonymized).',
                'priority': 10
            }
        ])
        
        # Real Estate scenarios (existing industry)
        scenarios.extend([
            {
                'industry': 'real_estate',
                'scenario_type': 'use_case',
                'title': 'Property Price Prediction',
                'description': 'Predict property prices based on location, features, and market trends.',
                'priority': 10,
                'icon_name': '010-new house.png'
            },
            {
                'industry': 'real_estate',
                'scenario_type': 'competition_idea',
                'title': 'Housing Price Prediction',
                'description': 'Predict housing prices using property features and location data.',
                'priority': 10,
                'details': {'metric': 'RMSE', 'submission_format': 'CSV'}
            }
        ])
        
        return scenarios
