"""
Beep.AI.Server Client - Integration with Beep.AI.Server
"""
import requests
import logging
from typing import Dict, Optional, Any, List
import os

logger = logging.getLogger(__name__)


class AIServerClient:
    """Client for Beep.AI.Server API"""
    
    def __init__(self, base_url: str = None, api_key: Optional[str] = None):
        """Initialize AI Server client"""
        self.base_url = (base_url or os.getenv('AISERVER_URL', 'http://127.0.0.1:5000')).rstrip('/')
        self.api_key = api_key or os.getenv('AISERVER_API_KEY', '')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to AI Server"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=60, **kwargs)
            return response.json()
        except Exception as e:
            logger.error(f"AI Server request failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def health_check(self) -> bool:
        """Check if AI Server is accessible"""
        try:
            result = self._request('GET', '/api/v1/health')
            return result.get('status') == 'ok'
        except:
            return False
    
    def generate_description(self, text: str, context: str = '') -> Optional[str]:
        """Generate description using LLM"""
        return None
    
    def get_model_recommendations(self, dataset_info: Dict) -> List[Dict]:
        """Get model recommendations based on dataset"""
        return []
