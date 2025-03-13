import os
import firebase_admin
from firebase_admin import credentials
import logging

logger = logging.getLogger(__name__)

_firebase_app = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK if it hasn't been initialized already.
    Uses Application Default Credentials.
    """
    global _firebase_app
    
    if _firebase_app is None:
        try:
            # Print environment variable for debugging
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            print(f"Loading credentials from: {cred_path}")
            
            # Initialize Firebase with application default credentials
            _firebase_app = firebase_admin.initialize_app()
            
            # Print app info for debugging
            print(f"Firebase app name: {_firebase_app.name}")
            print(f"Firebase project ID: {_firebase_app.project_id}")
            print("Firebase initialized with application default credentials")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Firebase: {str(e)}")
    
    return _firebase_app