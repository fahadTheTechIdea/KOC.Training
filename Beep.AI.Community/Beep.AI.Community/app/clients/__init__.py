"""
External Service Clients Package
"""
from app.clients.aiserver_client import AIServerClient
from app.clients.identity_server_client import IdentityServerClient, get_identity_server_client

__all__ = ['AIServerClient', 'IdentityServerClient', 'get_identity_server_client']
