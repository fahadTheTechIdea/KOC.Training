"""
Database Provider Helper - Multi-database support utilities
"""
import logging
from typing import Optional, Dict, Tuple, List

from app.utils.constants import (
    DB_PROVIDER_SQLITE,
    DB_PROVIDER_POSTGRESQL,
    DB_PROVIDER_MYSQL,
    DB_PROVIDER_MSSQL,
    DB_PROVIDER_ORACLE,
    DB_PROVIDER_FIREBIRD,
    DB_PREFIX_SQLITE,
    DB_PREFIX_POSTGRESQL,
    DB_PREFIX_POSTGRES,
    DB_PREFIX_MYSQL,
    DB_PREFIX_MYSQL_PYMYSQL,
    DB_PREFIX_MARIADB,
    DB_PREFIX_MSSQL,
    DB_PREFIX_MSSQL_PYODBC,
    DB_PREFIX_ORACLE,
    DB_PREFIX_FIREBIRD,
    DB_PORT_POSTGRESQL,
    DB_PORT_MYSQL,
    DB_PORT_MSSQL,
    DB_PORT_ORACLE,
    DB_PORT_FIREBIRD,
    DB_CONNECTION_TIMEOUT,
    ERROR_DB_CONNECTION_STRING_EMPTY,
    ERROR_DB_DRIVER_NOT_INSTALLED
)

logger = logging.getLogger(__name__)


class DatabaseProviderHelper:
    """Helper class for managing multiple database providers"""
    
    # Validation rules for each provider
    VALIDATION_RULES = {
        DB_PROVIDER_SQLITE: {
            'prefixes': [DB_PREFIX_SQLITE],
            'optional_prefixes': [],
            'requires_driver': False,
            'error_msg': f"SQLite connection string must start with '{DB_PREFIX_SQLITE}'"
        },
        DB_PROVIDER_POSTGRESQL: {
            'prefixes': [DB_PREFIX_POSTGRESQL, DB_PREFIX_POSTGRES],
            'optional_prefixes': [],
            'requires_driver': False,
            'error_msg': f"PostgreSQL connection string must start with '{DB_PREFIX_POSTGRESQL}' or '{DB_PREFIX_POSTGRES}'"
        },
        DB_PROVIDER_MYSQL: {
            'prefixes': [DB_PREFIX_MYSQL_PYMYSQL],
            'optional_prefixes': [DB_PREFIX_MARIADB],
            'contains_keywords': ['mysql'],
            'requires_driver': True,
            'driver_format': DB_PREFIX_MYSQL_PYMYSQL,
            'error_msg': "MySQL connection string should use 'mysql+pymysql://' format or start with 'mariadb://'"
        },
        DB_PROVIDER_MSSQL: {
            'prefixes': [DB_PREFIX_MSSQL, DB_PREFIX_MSSQL_PYODBC],
            'optional_prefixes': [],
            'contains_keywords': ['sqlserver', DB_PREFIX_MSSQL_PYODBC],
            'requires_driver': False,
            'error_msg': f"SQL Server connection string must start with '{DB_PREFIX_MSSQL}' or '{DB_PREFIX_MSSQL_PYODBC}'"
        },
        DB_PROVIDER_ORACLE: {
            'prefixes': [DB_PREFIX_ORACLE],
            'optional_prefixes': [],
            'contains_keywords': ['oracle'],
            'requires_driver': False,
            'error_msg': f"Oracle connection string must start with '{DB_PREFIX_ORACLE}'"
        },
        DB_PROVIDER_FIREBIRD: {
            'prefixes': [DB_PREFIX_FIREBIRD],
            'optional_prefixes': [],
            'requires_driver': False,
            'error_msg': f"Firebird connection string must start with '{DB_PREFIX_FIREBIRD}'"
        }
    }
    
    SUPPORTED_PROVIDERS = {
        DB_PROVIDER_SQLITE: {
            'name': 'SQLite',
            'description': 'Local file database (development/small deployments)',
            'driver': 'built-in',
            'connection_string_example': 'sqlite:///community.db',
            'default_port': None
        },
        DB_PROVIDER_POSTGRESQL: {
            'name': 'PostgreSQL',
            'description': 'Enterprise-grade open-source database',
            'driver': 'psycopg2-binary',
            'connection_string_example': 'postgresql://user:password@localhost:5432/community',
            'default_port': DB_PORT_POSTGRESQL
        },
        DB_PROVIDER_MYSQL: {
            'name': 'MySQL/MariaDB',
            'description': 'Popular open-source database',
            'driver': 'PyMySQL',
            'connection_string_example': 'mysql+pymysql://user:password@localhost:3306/community',
            'default_port': DB_PORT_MYSQL
        },
        DB_PROVIDER_MSSQL: {
            'name': 'SQL Server',
            'description': 'Microsoft SQL Server',
            'driver': 'pyodbc',
            'connection_string_example': 'mssql+pyodbc://user:password@localhost:1433/community?driver=ODBC+Driver+17+for+SQL+Server',
            'default_port': DB_PORT_MSSQL
        },
        DB_PROVIDER_ORACLE: {
            'name': 'Oracle',
            'description': 'Oracle Database',
            'driver': 'oracledb',
            'connection_string_example': 'oracle://user:password@localhost:1521/XE',
            'default_port': DB_PORT_ORACLE
        },
        DB_PROVIDER_FIREBIRD: {
            'name': 'Firebird',
            'description': 'Open-source relational database',
            'driver': 'fdb',
            'connection_string_example': 'firebird://user:password@localhost:3050/path/to/database.fdb',
            'default_port': DB_PORT_FIREBIRD
        }
    }
    
    @classmethod
    def get_supported_providers(cls) -> Dict[str, Dict]:
        """Get all supported database providers"""
        return cls.SUPPORTED_PROVIDERS.copy()
    
    @classmethod
    def detect_provider_from_connection_string(cls, connection_string: str) -> Optional[str]:
        """
        Detect database provider from connection string using validation rules
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Provider name (sqlite, postgresql, mysql, etc.) or None if unknown
        """
        if not connection_string:
            return None
        
        conn_str_lower = connection_string.strip().lower()
        
        # Check each provider's validation rules
        for provider, rules in cls.VALIDATION_RULES.items():
            # Check prefixes
            for prefix in rules.get('prefixes', []):
                if conn_str_lower.startswith(prefix):
                    return provider
            
            # Check optional prefixes
            for prefix in rules.get('optional_prefixes', []):
                if conn_str_lower.startswith(prefix):
                    return provider
            
            # Check for keywords (for providers with flexible formats)
            keywords = rules.get('contains_keywords', [])
            if keywords:
                for keyword in keywords:
                    if keyword in conn_str_lower:
                        return provider
        
        return None
    
    @classmethod
    def validate_connection_string(cls, provider: str, connection_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate connection string format for a provider using validation rules
        
        Args:
            provider: Database provider name
            connection_string: Connection string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not connection_string:
            return False, ERROR_DB_CONNECTION_STRING_EMPTY
        
        provider = provider.lower()
        
        # Check if provider is supported
        if provider not in cls.VALIDATION_RULES:
            return False, f"Unknown provider: {provider}"
        
        rules = cls.VALIDATION_RULES[provider]
        conn_str_lower = connection_string.strip().lower()
        
        # Check prefixes
        valid_prefix = False
        for prefix in rules.get('prefixes', []):
            if conn_str_lower.startswith(prefix):
                valid_prefix = True
                break
        
        # Check optional prefixes if no main prefix matched
        if not valid_prefix:
            for prefix in rules.get('optional_prefixes', []):
                if conn_str_lower.startswith(prefix):
                    valid_prefix = True
                    break
        
        # Check keywords if no prefix matched
        if not valid_prefix:
            keywords = rules.get('contains_keywords', [])
            for keyword in keywords:
                if keyword in conn_str_lower:
                    valid_prefix = True
                    break
        
        if not valid_prefix:
            return False, rules.get('error_msg', 'Invalid connection string format')
        
        # Special validation for MySQL (must use pymysql driver format)
        if provider == DB_PROVIDER_MYSQL:
            if DB_PREFIX_MYSQL_PYMYSQL not in conn_str_lower and not conn_str_lower.startswith(DB_PREFIX_MARIADB):
                if 'mysql://' in conn_str_lower:
                    return False, rules.get('error_msg', 'Invalid MySQL connection string format')
        
        return True, None
    
    @classmethod
    def format_connection_string(cls, provider: str, host: str = None, port: int = None,
                                  database: str = None, username: str = None,
                                  password: str = None, **kwargs) -> str:
        """
        Format connection string from components
        
        Args:
            provider: Database provider name
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password
            **kwargs: Additional connection parameters
            
        Returns:
            Formatted connection string
        """
        provider = provider.lower()
        
        # Get provider info for defaults
        provider_info = cls.SUPPORTED_PROVIDERS.get(provider)
        if not provider_info:
            raise ValueError(f"Unsupported provider: {provider}")
        
        default_port = provider_info.get('default_port')
        
        if provider == DB_PROVIDER_SQLITE:
            db_path = database or 'community.db'
            return f'{DB_PREFIX_SQLITE}/{db_path}'
        
        if provider == DB_PROVIDER_POSTGRESQL:
            if not all([host, database, username, password]):
                raise ValueError("PostgreSQL requires host, database, username, and password")
            port = port or default_port or DB_PORT_POSTGRESQL
            return f'{DB_PREFIX_POSTGRESQL}{username}:{password}@{host}:{port}/{database}'
        
        if provider == DB_PROVIDER_MYSQL:
            if not all([host, database, username, password]):
                raise ValueError("MySQL requires host, database, username, and password")
            port = port or default_port or DB_PORT_MYSQL
            return f'{DB_PREFIX_MYSQL_PYMYSQL}{username}:{password}@{host}:{port}/{database}'
        
        if provider == DB_PROVIDER_MSSQL:
            if not all([host, database, username, password]):
                raise ValueError("SQL Server requires host, database, username, and password")
            port = port or default_port or DB_PORT_MSSQL
            driver = kwargs.get('driver', 'ODBC Driver 17 for SQL Server')
            driver_encoded = driver.replace(' ', '+')
            return f'{DB_PREFIX_MSSQL_PYODBC}{username}:{password}@{host}:{port}/{database}?driver={driver_encoded}'
        
        if provider == DB_PROVIDER_ORACLE:
            if not all([host, username, password]):
                raise ValueError("Oracle requires host, username, and password")
            port = port or default_port or DB_PORT_ORACLE
            service_name = database or kwargs.get('service_name', 'XE')
            return f'{DB_PREFIX_ORACLE}{username}:{password}@{host}:{port}/{service_name}'
        
        if provider == DB_PROVIDER_FIREBIRD:
            if not all([host, database, username, password]):
                raise ValueError("Firebird requires host, database, username, and password")
            port = port or default_port or DB_PORT_FIREBIRD
            return f'{DB_PREFIX_FIREBIRD}{username}:{password}@{host}:{port}/{database}'
        
        raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    def test_connection(cls, connection_string: str) -> Tuple[bool, Optional[str]]:
        """
        Test database connection with improved error handling
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            from sqlalchemy import create_engine, text
            
            is_sqlite = DB_PROVIDER_SQLITE in connection_string.lower()
            
            # Create engine with appropriate configuration
            connect_args = {}
            if not is_sqlite:
                connect_args['connect_timeout'] = DB_CONNECTION_TIMEOUT
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
                connect_args=connect_args
            )
            
            # Try to connect and execute simple query
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            
            logger.debug(f"Database connection test successful: {connection_string[:50]}...")
            return True, None
            
        except ImportError as e:
            error_msg = f"{ERROR_DB_DRIVER_NOT_INSTALLED}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            # Provide more specific error messages based on exception type
            error_type = type(e).__name__
            error_str = str(e)
            
            if 'OperationalError' in error_type:
                error_msg = f"Database connection failed. Please check connection string and database server status: {error_str}"
            elif 'AuthenticationFailed' in error_type or 'InvalidPassword' in error_type or 'password' in error_str.lower():
                error_msg = f"Authentication failed. Please check username and password: {error_str}"
            elif 'DoesNotExist' in error_type or 'UnknownDatabase' in error_type or 'database' in error_str.lower() and 'exist' in error_str.lower():
                error_msg = f"Database does not exist. Please create the database first: {error_str}"
            else:
                error_msg = f"Connection failed: {error_str}"
            
            logger.error(f"{error_msg} - Connection string: {connection_string[:50]}...")
            return False, error_msg
        finally:
            # Clean up engine
            try:
                if 'engine' in locals():
                    engine.dispose()
            except Exception:
                pass
    
    @classmethod
    def get_connection_string_example(cls, provider: str) -> str:
        """Get example connection string for a provider"""
        provider = provider.lower()
        provider_info = cls.SUPPORTED_PROVIDERS.get(provider)
        if provider_info:
            return provider_info['connection_string_example']
        return ''
