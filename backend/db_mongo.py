import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError

logger = logging.getLogger('smart_campus.mongo')

class MongoManager:
    """
    Thread-safe MongoDB Atlas Connection Manager for Smart Campus Analytics.
    Provides connection pooling, health checks, error resilience, and collection accessors.
    """
    _instance: Optional['MongoManager'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _is_connected: bool = False
    _last_error: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_connection_uri(cls) -> str:
        """
        Builds or extracts the MongoDB connection URI from environment variables.
        Supports standard Atlas SRV URIs or modular host/user/password variables.
        """
        uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
        if uri and uri.strip():
            return uri.strip()

        username = os.environ.get('MONGO_USERNAME') or os.environ.get('MONGO_USER')
        password = os.environ.get('MONGO_PASSWORD') or os.environ.get('MONGO_PASS')
        host = os.environ.get('MONGO_HOST') or os.environ.get('MONGO_CLUSTER_HOST')
        db_name = os.environ.get('MONGO_DB_NAME') or os.environ.get('MONGODB_DB_NAME', 'smart_campus_db')

        if username and password and host:
            # Construct standard MongoDB Atlas SRV URI
            return f"mongodb+srv://{username}:{password}@{host}/{db_name}?retryWrites=true&w=majority"
        
        # Local fallback if explicitly configured
        local_uri = os.environ.get('MONGO_LOCAL_URI', 'mongodb://localhost:27017/smart_campus_db')
        return local_uri

    @classmethod
    def get_database_name(cls) -> str:
        return os.environ.get('MONGODB_DB_NAME') or os.environ.get('MONGO_DB_NAME', 'smart_campus_db')

    def connect(self, uri: Optional[str] = None, timeout_ms: int = 4000) -> bool:
        """
        Establishes connection to MongoDB Atlas with connection pooling and timeout.
        """
        conn_uri = uri or self.get_connection_uri()
        db_name = self.get_database_name()

        try:
            # Configure MongoClient with sensible Atlas timeouts and pool limits
            self._client = MongoClient(
                conn_uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5,
                retryWrites=True,
                retryReads=True,
                appname="SmartCampusAnalytics"
            )

            # Health Check Ping
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            self._is_connected = True
            self._last_error = None
            logger.info(f"Successfully connected to MongoDB Atlas database: '{db_name}'")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            self._is_connected = False
            self._last_error = f"Connection timeout or failure: {str(err)}"
            logger.warning(f"MongoDB Atlas Connection Warning: {self._last_error}")
            return False
        except ConfigurationError as err:
            self._is_connected = False
            self._last_error = f"MongoDB Configuration error: {str(err)}"
            logger.warning(f"MongoDB Config Error: {self._last_error}")
            return False
        except Exception as err:
            self._is_connected = False
            self._last_error = f"Unexpected MongoDB error: {str(err)}"
            logger.warning(f"MongoDB Unexpected Error: {self._last_error}")
            return False

    def get_db(self) -> Optional[Database]:
        """
        Returns the active MongoDB database instance, connecting if needed.
        """
        if not self._is_connected or self._db is None:
            self.connect()
        return self._db if self._is_connected else None

    def get_collection(self, collection_name: str):
        """
        Returns the requested collection if connected, else None.
        """
        db = self.get_db()
        if db is not None:
            return db[collection_name]
        return None

    def get_status(self) -> Dict[str, Any]:
        """
        Returns real-time connection status, database metadata, and collection counts.
        """
        db = self.get_db()
        if not self._is_connected or db is None:
            return {
                'connected': False,
                'database': self.get_database_name(),
                'error': self._last_error or 'MongoDB not connected or credentials not configured',
                'collections': {},
                'timestamp': datetime.utcnow().isoformat()
            }

        try:
            collections = db.list_collection_names()
            stats = {}
            for col_name in ['students', 'academic_records', 'attendance_records', 'skills_learning', 'student_feedbacks', 'ai_recommendations']:
                if col_name in collections:
                    stats[col_name] = db[col_name].count_documents({})
                else:
                    stats[col_name] = 0

            return {
                'connected': True,
                'database': db.name,
                'collections_count': len(collections),
                'collection_stats': stats,
                'error': None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as err:
            return {
                'connected': False,
                'database': db.name if db else self.get_database_name(),
                'error': str(err),
                'collections': {},
                'timestamp': datetime.utcnow().isoformat()
            }

    def close(self):
        """Closes the MongoClient connection cleanly."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._db = None
            self._is_connected = False


# Global MongoDB Manager Instance
mongo_manager = MongoManager()

def get_mongo_db() -> Optional[Database]:
    return mongo_manager.get_db()

def get_mongo_collection(name: str):
    return mongo_manager.get_collection(name)
