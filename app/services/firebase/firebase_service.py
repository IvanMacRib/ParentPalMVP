# app/services/firebase/firebase_service.py

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

_firebase_app = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK if it hasn't been initialized already.
    """
    global _firebase_app
    
    if _firebase_app is None:
        try:
            # Use the service account file directly
            cred_path = "/Users/ivanribeiro/ParentPalMVP/config/firebase/parentpal-service-account.json"
            print(f"Using credentials file: {cred_path}")
            
            if not os.path.exists(cred_path):
                raise Exception(f"Credentials file not found at: {cred_path}")
                
            try:
                with open(cred_path, 'r') as f:
                    cred_dict = json.load(f)
                cred = credentials.Certificate(cred_dict)
                _firebase_app = firebase_admin.initialize_app(cred)
                print("Firebase initialized with credentials file")
            except Exception as file_error:
                print(f"Error reading credentials file: {file_error}")
                raise
        except Exception as init_error:
            print(f"Failed to initialize Firebase: {init_error}")
            raise
    
    return _firebase_app

def get_firestore_client():
    """
    Get a Firestore client
    """
    if _firebase_app is None:
        initialize_firebase()
    
    return firestore.client()