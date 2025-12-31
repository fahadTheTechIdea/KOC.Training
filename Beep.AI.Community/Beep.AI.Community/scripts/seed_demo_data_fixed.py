"""
Script to seed comprehensive demo data for the Community platform
All demo data is tagged with industry="demo" for easy identification
Run: python -m scripts.seed_demo_data
Or: flask seed-demo-data
"""
import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.user import User, UserProfile, ROLE_USER
from app.models.competition import Competition, CompetitionParticipant
from app.models.submission import Submission
from app.models.dataset import Dataset
from app.models.notebook import Notebook
from app.models.discussion import Discussion, DiscussionReply, DiscussionUpvote
from app.models.model_registry import ModelRegistry
from app.models.activity import Activity

# Demo data configuration
DEMO_INDUSTRY = "demo"
DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@koc.training"
DEMO_PASSWORD = "demo123"

# Sample names for demo users
DEMO_USER_NAMES = [
    ("Ahmed", "Al-Sabah"), ("Fatima", "Al-Khaled"), ("Mohammed", "Al-Rashid"),
    ("Noura", "Al-Mansouri"), ("Khalid", "Al-Dosari"), ("Layla", "Al-Hamad"),
    ("Omar", "Al-Mutairi"), ("Sara", "Al-Otaibi"), ("Yusuf", "Al-Shammari"),
    ("Amina", "Al-Fahad"), ("Hassan", "Al-Ghanim"), ("Mariam", "Al-Sabah"),
    ("Ibrahim", "Al-Kharafi"), ("Zainab", "Al-Mazidi"), ("Tariq", "Al-Ahmad")
]

# Competition templates
COMPETITION_TEMPLATES = [
    {
        "title": "Oil Production Prediction Challenge",
        "description": "Predict daily oil production based on well characteristics, geological data, and operational parameters. This competition focuses on regression techniques to forecast production volumes for KOC's oil fields.",
        "evaluation_metric": "RMSE",
        "task_type": "regression",
        "max_submissions_per_day": 5,
        "max_total_submissions": 100,
        "prize_description": "Winner receives recognition and potential collaboration opportunities with KOC's production team.",
        "is_active": True,
        "days_offset_start": -30,
        "days_offset_end": 30
    },
    {
        "title": "Medical Diagnosis Classification",
        "description": "Classify medical conditions from patient records and diagnostic data. Help improve healthcare outcomes by accurately identifying conditions from structured and unstructured medical data.",
        "evaluation_metric": "F1-Score",
        "task_type": "classification",
        "max_submissions_per_day": 3,
        "max_total_submissions": 50,
        "prize_description": "Top performers will be featured in KOC's healthcare innovation showcase.",
        "is_active": True,
        "days_offset_start": -15,
        "days_offset_end": 45
    },
    {
        "title": "Energy Consumption Forecasting",
        "description": "Forecast energy consumption patterns using time series analysis. Predict future energy demand to optimize resource allocation and reduce waste across KOC facilities.",
        "evaluation_metric": "MAE",
        "task_type": "regression",
        "max_submissions_per_day": 10,
        "max_total_submissions": 200,
        "prize_description": "Best models will be considered for implementation in KOC's energy management systems.",
        "is_active": True,
        "days_offset_start": -20,
        "days_offset_end": 40
    },
    {
        "title": "Reservoir Analysis ML Competition",
        "description": "Multi-output regression challenge to predict reservoir characteristics including porosity, permeability, and saturation levels from well log data.",
        "evaluation_metric": "RMSE",
        "task_type": "regression",
        "max_submissions_per_day": 5,
        "max_total_submissions": 100,
        "prize_description": "Winners will be invited to present their solutions to KOC's reservoir engineering team.",
        "is_active": True,
        "days_offset_start": -10,
        "days_offset_end": 50
    },
    {
        "title": "Smart Grid Optimization",
        "description": "Classify optimal grid configurations for energy distribution. Use machine learning to identify the best grid setup for minimizing losses and maximizing efficiency.",
        "evaluation_metric": "Accuracy",
        "task_type": "classification",
        "max_submissions_per_day": 7,
        "max_total_submissions": 150,
        "prize_description": "Top solutions may be integrated into KOC's smart grid infrastructure.",
        "is_active": True,
        "days_offset_start": -5,
        "days_offset_end": 55
    },
    {
        "title": "Well Performance Prediction",
        "description": "Predict well performance metrics including flow rates and pressure profiles. This ended competition showcased excellent solutions for production optimization.",
        "evaluation_metric": "RMSE",
        "task_type": "regression",
        "max_submissions_per_day": 5,
        "max_total_submissions": 100,
        "prize_description": "Competition completed. Winners announced.",
        "is_active": False,
        "days_offset_start": -120,
        "days_offset_end": -30
    },
    {
        "title": "Patient Readmission Prediction",
        "description": "Predict patient readmission risk within 30 days of discharge. Help healthcare providers identify high-risk patients for better care management.",
        "evaluation_metric": "F1-Score",
        "task_type": "classification",
        "max_submissions_per_day": 3,
        "max_total_submissions": 50,
        "prize_description": "Competition completed successfully.",
        "is_active": False,
        "days_offset_start": -90,
        "days_offset_end": -20
    },
    {
        "title": "Renewable Energy Forecasting",
        "description": "Forecast renewable energy generation from solar and wind sources. Critical for grid stability and energy planning in KOC's renewable initiatives.",
        "evaluation_metric": "MAE",
        "task_type": "regression",
        "max_submissions_per_day": 8,
        "max_total_submissions": 180,
        "prize_description": "Competition ended. Top models demonstrated excellent forecasting accuracy.",
        "is_active": False,
        "days_offset_start": -100,
        "days_offset_end": -10
    },
    {
        "title": "Equipment Failure Prediction",
        "description": "Predict equipment failures before they occur using sensor data and maintenance records. Enable predictive maintenance strategies for KOC operations.",
        "evaluation_metric": "F1-Score",
        "task_type": "classification",
        "max_submissions_per_day": 5,
        "max_total_submissions": 100,
        "prize_description": "Best models will be evaluated for real-world deployment.",
        "is_active": True,
        "days_offset_start": -25,
        "days_offset_end": 35
    },
    {
        "title": "Water Quality Classification",
        "description": "Classify water quality levels from chemical and biological measurements. Support environmental monitoring and safety compliance for KOC facilities.",
        "evaluation_metric": "Accuracy",
        "task_type": "classification",
        "max_submissions_per_day": 4,
        "max_total_submissions": 80,
        "prize_description": "Top performers will be recognized in KOC's sustainability report.",
        "is_active": True,
        "days_offset_start": -18,
        "days_offset_end": 42
    }
]

# Dataset templates
DATASET_TEMPLATES = [
    {
        "title": "KOC Oil Production Dataset 2024",
        "description": "Comprehensive dataset containing daily oil production data from multiple KOC fields, including well characteristics, geological features, and operational parameters.",
        "category": "raw_data",
        "file_format": "CSV",
        "file_size": 15728640,  # ~15 MB
        "tags": "oil,production,wells,geology"
    },
    {
        "title": "Medical Records Sample Data",
        "description": "Anonymized medical records dataset with patient demographics, diagnoses, treatments, and outcomes. Suitable for healthcare ML research.",
        "category": "processed",
        "file_format": "CSV",
        "file_size": 8388608,  # ~8 MB
        "tags": "healthcare,medical,records,diagnosis"
    },
    {
        "title": "Energy Consumption Historical Data",
        "description": "Historical energy consumption data from KOC facilities over the past 5 years, including hourly readings and facility metadata.",
        "category": "raw_data",
        "file_format": "CSV",
        "file_size": 31457280,  # ~30 MB
        "tags": "energy,consumption,time-series,facilities"
    },
    {
        "title": "Reservoir Characteristics Dataset",
        "description": "Detailed reservoir data including porosity, permeability, saturation, and pressure measurements from multiple oil fields.",
        "category": "processed",
        "file_format": "CSV",
        "file_size": 10485760,  # ~10 MB
        "tags": "reservoir,geology,petroleum,engineering"
    },
    {
        "title": "Patient Demographics Dataset",
        "description": "Demographic and health indicator data for patient populations, useful for healthcare analytics and predictive modeling.",
        "category": "raw_data",
        "file_format": "CSV",
        "file_size": 5242880,  # ~5 MB
        "tags": "healthcare,demographics,patients,analytics"
    },
    {
        "title": "Smart Meter Readings",
        "description": "High-frequency smart meter readings from residential and commercial installations, including consumption patterns and anomalies.",
        "category": "raw_data",
        "file_format": "CSV",
        "file_size": 20971520,  # ~20 MB
        "tags": "smart-meters,energy,iot,consumption"
    },
    {
        "title": "Equipment Sensor Data",
        "description": "Time-series sensor data from industrial equipment including temperature, pressure, vibration, and operational status indicators.",
        "category": "raw_data",
        "file_format": "CSV",
        "file_size": 26214400,  # ~25 MB
        "tags": "equipment,sensors,iot,maintenance"
    },
    {
        "title": "Water Quality Measurements",
        "description": "Comprehensive water quality dataset with chemical, biological, and physical measurements from various sampling locations.",
        "category": "processed",
        "file_format": "CSV",
        "file_size": 6291456,  # ~6 MB
        "tags": "water-quality,environmental,chemistry,monitoring"
    }
]

# Project templates
PROJECT_TEMPLATES = [
    {
        "title": "Predictive Maintenance for Oil Rigs",
        "description": "A comprehensive ML project for predicting equipment failures in oil rig operations using sensor data and maintenance history.",
        "category": "classification",
        "language": "python",
        "tags": "predictive-maintenance,oil-rigs,equipment,ml"
    },
    {
        "title": "Medical Image Classification",
        "description": "Deep learning project for classifying medical images using convolutional neural networks. Includes preprocessing and augmentation techniques.",
        "category": "classification",
        "language": "python",
        "tags": "medical-imaging,cnn,deep-learning,healthcare"
    },
    {
        "title": "Energy Demand Forecasting Model",
        "description": "Time series forecasting model using LSTM networks to predict energy demand patterns. Includes feature engineering and model evaluation.",
        "category": "time_series",
        "language": "python",
        "tags": "energy,forecasting,lstm,time-series"
    },
    {
        "title": "Reservoir Simulation Analysis",
        "description": "Advanced reservoir analysis using machine learning to predict reservoir behavior and optimize extraction strategies.",
        "category": "regression",
        "language": "python",
        "tags": "reservoir,simulation,petroleum,optimization"
    },
    {
        "title": "Patient Risk Assessment Tool",
        "description": "ML-based tool for assessing patient risk factors and predicting health outcomes using electronic health records.",
        "category": "classification",
        "language": "python",
        "tags": "healthcare,risk-assessment,patients,analytics"
    },
    {
        "title": "Smart Grid Load Balancing",
        "description": "Optimization project for balancing electrical loads across smart grid networks using reinforcement learning techniques.",
        "category": "optimization",
        "language": "python",
        "tags": "smart-grid,optimization,reinforcement-learning,energy"
    },
    {
        "title": "Oil Well Production Optimization",
        "description": "Data-driven approach to optimizing oil well production rates using ensemble methods and feature importance analysis.",
        "category": "regression",
        "language": "python",
        "tags": "oil-production,optimization,ensemble-methods,petroleum"
    },
    {
        "title": "Water Quality Monitoring System",
        "description": "Real-time water quality classification system using sensor data and machine learning for environmental monitoring.",
        "category": "classification",
        "language": "python",
        "tags": "water-quality,monitoring,environmental,classification"
    },
    {
        "title": "Equipment Anomaly Detection",
        "description": "Unsupervised learning project for detecting anomalies in equipment sensor data using autoencoders and isolation forests.",
        "category": "anomaly_detection",
        "language": "python",
        "tags": "anomaly-detection,equipment,sensors,unsupervised-learning"
    },
    {
        "title": "Healthcare Resource Allocation",
        "description": "ML model for optimizing healthcare resource allocation based on patient demand patterns and historical data.",
        "category": "optimization",
        "language": "python",
        "tags": "healthcare,resource-allocation,optimization,analytics"
    }
]

# Discussion templates
DISCUSSION_TEMPLATES = [
    {
        "title": "How to improve model accuracy in Oil Production competition?",
        "content": "I'm struggling to get below 0.15 RMSE. I've tried feature engineering and different algorithms but can't seem to break through. Any tips from experienced participants?",
        "topic_type": "competition",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Best practices for time series forecasting",
        "content": "What are the best practices for handling time series data in the Energy Consumption Forecasting competition? Should I use LSTM, ARIMA, or other methods?",
        "topic_type": "general",
        "is_solved": True,
        "is_pinned": True
    },
    {
        "title": "Feature engineering tips for medical classification",
        "content": "Looking for advice on feature engineering for the Medical Diagnosis Classification competition. What features have worked well for others?",
        "topic_type": "competition",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Sharing my winning solution approach",
        "content": "I'd like to share the approach I used for the Well Performance Prediction competition. Happy to discuss and answer questions!",
        "topic_type": "competition",
        "is_solved": True,
        "is_pinned": True
    },
    {
        "title": "Dataset quality issues",
        "content": "I noticed some missing values in the Reservoir Characteristics Dataset. How should I handle them? Imputation or removal?",
        "topic_type": "dataset",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Model deployment best practices",
        "content": "What are the best practices for deploying ML models in production environments? Any KOC-specific considerations?",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Cross-validation strategies",
        "content": "What cross-validation strategy works best for small datasets? I'm working with limited medical records data.",
        "topic_type": "general",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Hyperparameter tuning tips",
        "content": "Looking for advice on hyperparameter tuning. Should I use grid search, random search, or Bayesian optimization?",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Project showcase: Predictive Maintenance System",
        "content": "I've published my predictive maintenance project. Check it out and let me know what you think! Open to feedback and collaboration.",
        "topic_type": "project",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Data preprocessing pipeline",
        "content": "What's your typical data preprocessing pipeline? I'm looking to standardize my approach across different competitions.",
        "topic_type": "general",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Handling imbalanced datasets",
        "content": "The Medical Diagnosis Classification competition has imbalanced classes. What techniques work best? SMOTE, class weights, or other methods?",
        "topic_type": "competition",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Ensemble methods discussion",
        "content": "Let's discuss ensemble methods! What combinations have worked well for you? Stacking, blending, or voting?",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Model interpretability in healthcare",
        "content": "How important is model interpretability in healthcare applications? Should we prioritize accuracy or explainability?",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Competition deadline approaching",
        "content": "The Oil Production Prediction Challenge deadline is coming up! What are your final strategies?",
        "topic_type": "competition",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Sharing useful datasets",
        "content": "I've uploaded a cleaned version of the energy consumption data with additional features. Feel free to use it!",
        "topic_type": "dataset",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Getting started with ML at KOC",
        "content": "New to machine learning? This is a great place to start! Ask questions and learn from the community.",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": True
    },
    {
        "title": "Model evaluation metrics explained",
        "content": "Let's discuss different evaluation metrics: when to use RMSE vs MAE, accuracy vs F1-score, etc. Understanding metrics is crucial!",
        "topic_type": "general",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Collaboration opportunities",
        "content": "Looking for teammates for the upcoming Smart Grid Optimization competition. Anyone interested in collaborating?",
        "topic_type": "competition",
        "is_solved": False,
        "is_pinned": False
    },
    {
        "title": "Best ML libraries for KOC projects",
        "content": "What ML libraries and frameworks do you recommend for KOC-specific projects? scikit-learn, TensorFlow, PyTorch, or others?",
        "topic_type": "general",
        "is_solved": True,
        "is_pinned": False
    },
    {
        "title": "Success story: From competition to production",
        "content": "I'm excited to share that my competition solution is being evaluated for production deployment! Happy to answer questions about the process.",
        "topic_type": "general",
        "is_solved": False,
        "is_pinned": True
    }
]

# Reply templates
REPLY_TEMPLATES = [
    "Great question! I found that feature engineering with domain knowledge really helped. Try incorporating geological features if available.",
    "For time series, I recommend starting with LSTM but also trying Prophet or ARIMA as baselines. Ensemble them for best results.",
    "I used SMOTE for handling imbalanced classes and it improved my F1-score significantly. Also consider adjusting class weights.",
    "Thanks for sharing! I'll check out your project. The approach looks interesting.",
    "For missing values, I'd suggest using domain-specific imputation methods rather than simple mean/median replacement.",
    "In production, model monitoring is crucial. Set up alerts for data drift and performance degradation.",
    "For small datasets, I use stratified k-fold cross-validation with k=5 or k=10 depending on sample size.",
    "I prefer Bayesian optimization (Optuna) for hyperparameter tuning. It's more efficient than grid search.",
    "Nice project! Have you considered adding more features for equipment age and maintenance history?",
    "My typical pipeline: data cleaning → feature engineering → scaling → model training → evaluation → deployment.",
    "For imbalanced data, I combine SMOTE with class weights. Also try focal loss if using neural networks.",
    "I've had success with stacking Random Forest, XGBoost, and LightGBM. The diversity helps a lot.",
    "In healthcare, interpretability is often required for regulatory compliance. Consider SHAP values or LIME.",
    "Final tip: ensemble your best models and submit early to avoid last-minute issues!",
    "Thanks for sharing the dataset! I'll give it a try in my next submission.",
    "Welcome! Don't hesitate to ask questions. The community is very helpful here.",
    "RMSE penalizes large errors more, MAE treats all errors equally. Use RMSE when large errors are critical.",
    "I'm interested! Let's discuss our approaches and see if we can collaborate.",
    "For KOC projects, I recommend scikit-learn for traditional ML and PyTorch for deep learning. Both are versatile.",
    "Congratulations! That's amazing. Can you share more about the evaluation process?"
]


def create_demo_user() -> User:
    """Create or get the main demo user"""
    user = User.query.filter_by(username=DEMO_USERNAME).first()
    if not user:
        user = User(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            role=ROLE_USER,
            is_active=True
        )
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            display_name="Demo User",
            bio="Demo account for exploring the KOC Training Platform. This account showcases all platform features.",
            location="Kuwait",
            organization="KOC",
            skills="Machine Learning, Data Science, Python"
        )
        db.session.add(profile)
        print(f"  [OK] Created demo user: {DEMO_USERNAME}")
    else:
        print(f"  [OK] Demo user already exists: {DEMO_USERNAME}")
    return user


def create_demo_users(count: int = 12) -> List[User]:
    """Create additional demo users"""
    users = []
    existing_usernames = {u.username for u in User.query.all()}
    
    for i, (first_name, last_name) in enumerate(DEMO_USER_NAMES[:count], 1):
        username = f"demo_user_{i}"
        if username in existing_usernames:
            user = User.query.filter_by(username=username).first()
            users.append(user)
            continue
            
        email = f"{username}@koc.training"
        user = User(
            username=username,
            email=email,
            role=ROLE_USER,
            is_active=True
        )
        user.set_password("demo123")
        db.session.add(user)
        db.session.flush()
        
        # Create profile with varying completion
        has_avatar = random.random() > 0.4
        profile = UserProfile(
            user_id=user.id,
            display_name=f"{first_name} {last_name}",
            bio=f"ML enthusiast working on {random.choice(['oil & gas', 'healthcare', 'energy'])} projects at KOC." if random.random() > 0.3 else None,
            location=random.choice(["Kuwait", "Ahmadi", "Mina Abdullah", None]),
            organization="KOC" if random.random() > 0.2 else None,
            skills=random.choice(["Python, ML", "Data Science, Statistics", "Deep Learning, TensorFlow", None])
        )
        db.session.add(profile)
        users.append(user)
    
    print(f"  [OK] Created {len([u for u in users if u.id])} demo users")
    return users


def seed_competitions(demo_users: List[User]) -> List[Competition]:
    """Seed competitions with participants"""
    competitions = []
    existing_titles = {c.title for c in Competition.query.filter_by(industry=DEMO_INDUSTRY).all()}
    
    for template in COMPETITION_TEMPLATES:
        if template["title"] in existing_titles:
            comp = Competition.query.filter_by(title=template["title"], industry=DEMO_INDUSTRY).first()
            competitions.append(comp)
            continue
            
        now = datetime.utcnow()
        start_date = now + timedelta(days=template["days_offset_start"])
        end_date = now + timedelta(days=template["days_offset_end"])
        
        organizer = random.choice(demo_users)
        
        competition = Competition(
            title=template["title"],
            description=template["description"],
            organizer_id=organizer.id,
            industry=DEMO_INDUSTRY,
            evaluation_metric=template["evaluation_metric"],
            task_type=template["task_type"],
            start_date=start_date,
            end_date=end_date,
            max_submissions_per_day=template["max_submissions_per_day"],
            max_total_submissions=template["max_total_submissions"],
            prize_description=template["prize_description"],
            is_active=template["is_active"],
            leaderboard_type=random.choice(["public", "public"]),  # Mostly public
            participant_count=0,
            submission_count=0
        )
        db.session.add(competition)
        db.session.flush()
        competitions.append(competition)
    
    print(f"  [OK] Created {len(competitions)} competitions")
    return competitions


def seed_participants_and_submissions(competitions: List[Competition], demo_users: List[User]) -> None:
    """Seed competition participants and submissions"""
    total_submissions = 0
    
    for competition in competitions:
        # Select participants (15-25 per competition)
        num_participants = random.randint(15, 25)
        participants = random.sample(demo_users, min(num_participants, len(demo_users)))
        
        # Create participant records
        existing_participants = {
            (cp.competition_id, cp.user_id)
            for cp in CompetitionParticipant.query.filter_by(competition_id=competition.id).all()
        }
        
        for user in participants:
            if (competition.id, user.id) not in existing_participants:
                participant = CompetitionParticipant(
                    competition_id=competition.id,
                    user_id=user.id,
                    joined_at=competition.start_date + timedelta(days=random.randint(0, 5))
                )
                db.session.add(participant)
        
        db.session.flush()
        
        # Create submissions for each participant
        all_submissions = []
        for user in participants:
            # Each user makes 2-8 submissions
            num_submissions = random.randint(2, 8)
            best_score = None
            
            for i in range(num_submissions):
                # Generate realistic scores based on task type
                if competition.task_type == "regression":
                    # RMSE/MAE: lower is better, range 0.05-0.5
                    base_score = random.uniform(0.05, 0.5)
                    score = base_score * (1 - i * 0.1)  # Improve over time
                else:
                    # Classification: higher is better, range 0.6-0.98
                    base_score = random.uniform(0.6, 0.98)
                    score = base_score + (i * 0.02)  # Improve over time
                    score = min(score, 0.98)
                
                if best_score is None or (competition.task_type == "regression" and score < best_score) or \
                   (competition.task_type != "regression" and score > best_score):
                    best_score = score
                
                submission_date = competition.start_date + timedelta(
                    days=random.randint(1, max(1, (competition.end_date - competition.start_date).days - 1))
                )
                
                submission = Submission(
                    competition_id=competition.id,
                    user_id=user.id,
                    score=round(score, 4),
                    status="evaluated" if competition.is_active or submission_date < competition.end_date else "evaluated",
                    submitted_at=submission_date,
                    evaluated_at=submission_date + timedelta(minutes=random.randint(5, 60))
                )
                all_submissions.append(submission)
                db.session.add(submission)
                total_submissions += 1
        
        db.session.flush()
        
        # Calculate and assign ranks
        if competition.task_type == "regression":
            # Lower is better
            all_submissions.sort(key=lambda s: s.score)
        else:
            # Higher is better
            all_submissions.sort(key=lambda s: s.score, reverse=True)
        
        for rank, submission in enumerate(all_submissions, 1):
            submission.rank = rank
        
        # Update competition counts
        competition.participant_count = len(participants)
        competition.submission_count = len(all_submissions)
    
    print(f"  [OK] Created participants and {total_submissions} submissions with rankings")
    db.session.commit()


def seed_datasets(demo_users: List[User]) -> List[Dataset]:
    """Seed sample datasets"""
    datasets = []
    existing_titles = {d.title for d in Dataset.query.filter_by(industry=DEMO_INDUSTRY).all()}
    
    for template in DATASET_TEMPLATES:
        if template["title"] in existing_titles:
            dataset = Dataset.query.filter_by(title=template["title"], industry=DEMO_INDUSTRY).first()
            datasets.append(dataset)
            continue
            
        owner = random.choice(demo_users)
        file_name = template["title"].lower().replace(" ", "_").replace(",", "") + ".csv"
        
        dataset = Dataset(
            title=template["title"],
            description=template["description"],
            owner_id=owner.id,
            file_path=f"/uploads/datasets/{file_name}",
            file_name=file_name,
            file_size=template["file_size"],
            file_format=template["file_format"],
            version=1,
            tags=template["tags"],
            category=template["category"],
            industry=DEMO_INDUSTRY,
            license="KOC Internal",
            is_public=random.random() > 0.2,  # 80% public
            download_count=random.randint(5, 150),
            view_count=random.randint(20, 500),
            rating=round(random.uniform(3.5, 5.0), 1)
        )
        db.session.add(dataset)
        datasets.append(dataset)
    
    print(f"  [OK] Created {len(datasets)} datasets")
    return datasets


def seed_projects(demo_users: List[User], competitions: List[Competition]) -> List[Notebook]:
    """Seed sample projects/notebooks"""
    projects = []
    existing_titles = {p.title for p in Notebook.query.filter_by(industry=DEMO_INDUSTRY).all()}
    
    for template in PROJECT_TEMPLATES:
        if template["title"] in existing_titles:
            project = Notebook.query.filter_by(title=template["title"], industry=DEMO_INDUSTRY).first()
            projects.append(project)
            continue
            
        owner = random.choice(demo_users)
        
        # Sample code content
        code_content = f"""
# {template['title']}
# {template['description']}

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load and preprocess data
# ... (demo code)

# Train model
# ... (demo code)

# Evaluate
# ... (demo code)
"""
        
        project = Notebook(
            title=template["title"],
            description=template["description"],
            owner_id=owner.id,
            language=template["language"],
            kernel_type="notebook",
            code_content=code_content,
            tags=json.dumps(template["tags"].split(",")),
            category=template["category"],
            industry=DEMO_INDUSTRY,
            is_public=True,
            fork_count=random.randint(0, 15),
            upvote_count=random.randint(0, 50),
            view_count=random.randint(10, 300),
            comment_count=random.randint(0, 20)
        )
        db.session.add(project)
        projects.append(project)
    
    print(f"  [OK] Created {len(projects)} projects")
    return projects


def seed_discussions(demo_users: List[User], competitions: List[Competition], 
                     datasets: List[Dataset], projects: List[Notebook]) -> List[Discussion]:
    """Seed discussions and replies"""
    discussions = []
    demo_user_ids = [u.id for u in demo_users]
    existing_titles = {d.title for d in Discussion.query.filter(Discussion.author_id.in_(demo_user_ids)).all()}
    
    for template in DISCUSSION_TEMPLATES:
        if template["title"] in existing_titles:
            continue
            
        author = random.choice(demo_users)
        
        # Determine topic_id based on topic_type
        topic_id = None
        if template["topic_type"] == "competition" and competitions:
            topic_id = random.choice(competitions).id
        elif template["topic_type"] == "dataset" and datasets:
            topic_id = random.choice(datasets).id
        elif template["topic_type"] == "project" and projects:
            topic_id = random.choice(projects).id
        
        discussion = Discussion(
            title=template["title"],
            content=template["content"],
            author_id=author.id,
            topic_type=template["topic_type"] if template["topic_type"] != "general" else None,
            topic_id=topic_id,
            is_pinned=template["is_pinned"],
            is_solved=template["is_solved"],
            upvote_count=0,
            reply_count=0
        )
        db.session.add(discussion)
        db.session.flush()
        discussions.append(discussion)
        
        # Add 1-4 replies per discussion
        num_replies = random.randint(1, 4)
        for _ in range(num_replies):
            reply_author = random.choice(demo_users)
            reply_content = random.choice(REPLY_TEMPLATES)
            
            reply = DiscussionReply(
                discussion_id=discussion.id,
                author_id=reply_author.id,
                content=reply_content
            )
            db.session.add(reply)
            discussion.reply_count += 1
        
        # Add some upvotes
        num_upvotes = random.randint(0, 10)
        upvoters = random.sample(demo_users, min(num_upvotes, len(demo_users)))
        for upvoter in upvoters:
            upvote = DiscussionUpvote(
                discussion_id=discussion.id,
                user_id=upvoter.id
            )
            db.session.add(upvote)
            discussion.upvote_count += 1
    
    print(f"  [OK] Created {len(discussions)} discussions with replies and upvotes")
    return discussions


def seed_models(demo_users: List[User], competitions: List[Competition]) -> List[ModelRegistry]:
    """Seed model registry entries"""
    models = []
    existing_names = {m.name for m in ModelRegistry.query.all()}
    
    model_templates = [
        {
            "name": "Oil Production Predictor v1.0",
            "description": "Random Forest model for predicting oil production rates. Trained on KOC well data.",
            "model_type": "regression",
            "framework": "scikit-learn",
            "metrics": {"rmse": 0.1245, "mae": 0.0892, "r2": 0.87}
        },
        {
            "name": "Medical Diagnosis Classifier",
            "description": "XGBoost classifier for medical diagnosis classification. Achieved 92% accuracy.",
            "model_type": "classification",
            "framework": "xgboost",
            "metrics": {"accuracy": 0.92, "f1_score": 0.89, "precision": 0.91}
        },
        {
            "name": "Energy Forecast LSTM",
            "description": "LSTM neural network for energy consumption forecasting. Time series model.",
            "model_type": "regression",
            "framework": "tensorflow",
            "metrics": {"mae": 0.045, "rmse": 0.062, "mape": 3.2}
        },
        {
            "name": "Reservoir Analysis Model",
            "description": "Multi-output regression model for reservoir characteristics prediction.",
            "model_type": "regression",
            "framework": "scikit-learn",
            "metrics": {"rmse": 0.156, "mae": 0.112, "r2": 0.82}
        },
        {
            "name": "Smart Grid Classifier",
            "description": "Neural network classifier for optimal grid configuration identification.",
            "model_type": "classification",
            "framework": "pytorch",
            "metrics": {"accuracy": 0.88, "f1_score": 0.85, "precision": 0.87}
        },
        {
            "name": "Equipment Failure Predictor",
            "description": "Gradient Boosting model for predicting equipment failures from sensor data.",
            "model_type": "classification",
            "framework": "scikit-learn",
            "metrics": {"accuracy": 0.91, "f1_score": 0.89, "recall": 0.93}
        }
    ]
    
    for template in model_templates:
        if template["name"] in existing_names:
            continue
            
        owner = random.choice(demo_users)
        
        model = ModelRegistry(
            name=template["name"],
            description=template["description"],
            owner_id=owner.id,
            model_type=template["model_type"],
            framework=template["framework"],
            model_file_path=f"/models/{template['name'].lower().replace(' ', '_')}.pkl",
            metrics=json.dumps(template["metrics"]),
            input_schema=json.dumps({"type": "array", "items": {"type": "number"}}),
            output_schema=json.dumps({"type": "number"}),
            is_public=True,
            download_count=random.randint(0, 50),
            view_count=random.randint(10, 200)
        )
        db.session.add(model)
        models.append(model)
    
    print(f"  [OK] Created {len(models)} model registry entries")
    return models


def seed_activities(demo_users: List[User], competitions: List[Competition],
                   discussions: List[Discussion], projects: List[Notebook]) -> None:
    """Seed activity logs"""
    activities = []
    activity_types = [
        "competition_joined", "submission_created", "discussion_created",
        "discussion_replied", "project_published", "dataset_uploaded",
        "model_published", "profile_updated"
    ]
    
    # Generate 50+ activities
    for _ in range(60):
        user = random.choice(demo_users)
        activity_type = random.choice(activity_types)
        
        resource_type = None
        resource_id = None
        activity_data = {}
        
        if activity_type == "competition_joined" and competitions:
            comp = random.choice(competitions)
            resource_type = "competition"
            resource_id = comp.id
            activity_data = {"competition_title": comp.title}
        elif activity_type == "submission_created" and competitions:
            comp = random.choice(competitions)
            resource_type = "submission"
            activity_data = {"competition_title": comp.title}
        elif activity_type == "discussion_created" and discussions:
            disc = random.choice(discussions)
            resource_type = "discussion"
            resource_id = disc.id
            activity_data = {"discussion_title": disc.title}
        elif activity_type == "discussion_replied" and discussions:
            disc = random.choice(discussions)
            resource_type = "discussion"
            resource_id = disc.id
            activity_data = {"discussion_title": disc.title}
        elif activity_type == "project_published" and projects:
            proj = random.choice(projects)
            resource_type = "project"
            resource_id = proj.id
            activity_data = {"project_title": proj.title}
        elif activity_type == "model_published":
            resource_type = "model"
            activity_data = {"model_name": "Demo Model"}
        
        activity = Activity(
            user_id=user.id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            activity_data=json.dumps(activity_data) if activity_data else None,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 90))
        )
        activities.append(activity)
        db.session.add(activity)
    
    print(f"  [OK] Created {len(activities)} activity logs")


def clear_demo_data():
    """Clear existing demo data (optional, for reset)"""
    print("Clearing existing demo data...")
    
    # Get demo user IDs
    demo_user_ids = [u.id for u in User.query.filter(User.username.like('demo%')).all()]
    
    if not demo_user_ids:
        print("  [OK] No demo data found to clear")
        return
    
    # Delete in reverse order of dependencies
    Activity.query.filter(Activity.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    DiscussionUpvote.query.filter(DiscussionUpvote.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    DiscussionReply.query.filter(DiscussionReply.author_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    Discussion.query.filter(Discussion.author_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    Submission.query.filter(Submission.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    CompetitionParticipant.query.filter(CompetitionParticipant.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    Competition.query.filter_by(industry=DEMO_INDUSTRY).delete(synchronize_session=False)
    Dataset.query.filter_by(industry=DEMO_INDUSTRY).delete(synchronize_session=False)
    Notebook.query.filter_by(industry=DEMO_INDUSTRY).delete(synchronize_session=False)
    ModelRegistry.query.filter(ModelRegistry.owner_id.in_(demo_user_ids)).delete(synchronize_session=False)
    
    # Delete demo users (except main demo user)
    User.query.filter(User.username.like('demo_user_%')).delete(synchronize_session=False)
    
    db.session.commit()
    print("  [OK] Demo data cleared")


def seed_all(reset: bool = False, users_only: bool = False):
    """Main function to seed all demo data"""
    print("=" * 60)
    print("Seeding Demo Data for KOC Training Platform")
    print("=" * 60)
    print()
    
    try:
        if reset:
            clear_demo_data()
        
        # Create demo users
        print("Creating demo users...")
        demo_user = create_demo_user()
        demo_users = [demo_user] + create_demo_users(12)
        db.session.commit()
        print()
        
        if users_only:
            print("Users-only mode: Skipping other data seeding")
            return
        
        # Seed competitions
        print("Seeding competitions...")
        competitions = seed_competitions(demo_users)
        db.session.commit()
        print()
        
        # Seed participants and submissions
        print("Seeding participants and submissions...")
        seed_participants_and_submissions(competitions, demo_users)
        db.session.commit()
        print()
        
        # Seed datasets
        print("Seeding datasets...")
        datasets = seed_datasets(demo_users)
        db.session.commit()
        print()
        
        # Seed projects
        print("Seeding projects...")
        projects = seed_projects(demo_users, competitions)
        db.session.commit()
        print()
        
        # Seed discussions
        print("Seeding discussions...")
        discussions = seed_discussions(demo_users, competitions, datasets, projects)
        db.session.commit()
        print()
        
        # Seed models
        print("Seeding models...")
        models = seed_models(demo_users, competitions)
        db.session.commit()
        print()
        
        # Seed activities
        print("Seeding activities...")
        seed_activities(demo_users, competitions, discussions, projects)
        db.session.commit()
        print()
        
        print("=" * 60)
        print("[SUCCESS] Demo data seeding completed!")
        print("=" * 60)
        print(f"Demo user: {DEMO_USERNAME} / {DEMO_PASSWORD}")
        print(f"Total users: {len(demo_users)}")
        print(f"Total competitions: {len(competitions)}")
        print(f"Total datasets: {len(datasets)}")
        print(f"Total projects: {len(projects)}")
        print(f"Total discussions: {len(discussions)}")
        print(f"Total models: {len(models)}")
        print("=" * 60)
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to seed demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed demo data for KOC Training Platform")
    parser.add_argument("--reset", action="store_true", help="Clear existing demo data before seeding")
    parser.add_argument("--users-only", action="store_true", help="Only seed demo users")
    args = parser.parse_args()
    
    app = create_app()
    with app.app_context():
        seed_all(reset=args.reset, users_only=args.users_only)


if __name__ == "__main__":
    main()

