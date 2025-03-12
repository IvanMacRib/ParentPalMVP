# app/services/firebase/profile_service.py

from firebase_admin import firestore
from .firebase_service import initialize_firebase
from ...models.profile_models import NameComponents, UserProfile, SpouseProfile, ChildProfile
import datetime

# Initialize Firebase first
initialize_firebase()

# Then get the Firestore client
db = firestore.client()

class ProfileService:
    def _parse_name(self, full_name: str) -> NameComponents:
        """Parse full name into components"""
        parts = full_name.split()
        if len(parts) == 2:
            return NameComponents(
                firstName=parts[0],
                lastName=parts[1]
            )
        elif len(parts) > 2:
            return NameComponents(
                firstName=parts[0],
                middleName=" ".join(parts[1:-1]),
                lastName=parts[-1]
            )
        else:
            raise ValueError("Name must include at least first and last name")

    def _create_profile_structure(self, userId: str):
        """Create initial profile structure"""
        user_ref = db.collection('users').document(userId)
        initial_data = {
            "name": {
                "firstName": "",
                "middleName": None,
                "lastName": ""
            },
            "dateOfBirth": "",
            "address": "",
            "profileComplete": False,
            "profileCreatedAt": datetime.datetime.now(),
            "profileUpdatedAt": datetime.datetime.now()
        }
        user_ref.set(initial_data)
        
        # Create subcollections but don't add documents
        user_ref.collection('spouse')  # Single document collection
        user_ref.collection('children')  # Multiple documents collection

    def getUserProfile(self, userId: str):
        """Get complete user profile including spouse and children"""
        try:
            # Get user document
            user_ref = db.collection('users').document(userId)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {"exists": False}
            
            # Get base profile data
            profile_data = user_doc.to_dict()
            
            # Get spouse data if it exists
            spouse_data = None
            spouse_docs = user_ref.collection('spouse').limit(1).get()
            spouse_list = list(spouse_docs)
            if spouse_list:
                spouse_data = spouse_list[0].to_dict()
            
            # Get children data if it exists
            children_data = []
            children_docs = user_ref.collection('children').get()
            for doc in children_docs:
                child = doc.to_dict()
                child['id'] = doc.id
                children_data.append(child)
            
            # Update children count
            self.updateChildrenCount(userId)
            
            # Combine all data
            full_profile = {
                "exists": True,
                "profile": profile_data,
                "spouse": spouse_data,
                "children": children_data
            }
            
            return full_profile
        
        except Exception as e:
            print(f"Error getting user profile: {e}")
            raise e

    def updateUserProfile(self, userId: str, profileData: dict) -> dict:
        """Update user profile with proper name handling"""
        try:
            # Handle name components if provided
            if "name" in profileData:
                # Name components are already in the correct format
                pass
            elif "fullName" in profileData:
                # Convert fullName to name components
                name_components = self._parse_name(profileData.pop("fullName"))
                profileData["name"] = name_components.dict()
            
            # Remove any legacy name fields
            for field in ["fullName"]:
                profileData.pop(field, None)
            
            user_ref = db.collection('users').document(userId)
            
            # Add timestamps
            profileData['profileUpdatedAt'] = datetime.datetime.now()
            if not user_ref.get().exists:
                profileData['profileCreatedAt'] = profileData['profileUpdatedAt']
                self._create_profile_structure(userId)
            
            # Validate data
            current_data = user_ref.get().to_dict() or {}
            updated_data = {**current_data, **profileData}
            validated_profile = UserProfile(**updated_data)
            
            # Set profile data
            user_ref.set(validated_profile.dict(), merge=True)
            
            # Update profile completion status
            self.updateProfileCompletionStatus(userId)
            
            return {"success": True}
        
        except Exception as e:
            print(f"Error updating user profile: {e}")
            raise e

    def addSpouse(self, userId: str, spouseData: dict) -> dict:
        """Add or update spouse information"""
        try:
            # Handle name components if provided
            if "name" in spouseData:
                # Name components are already in the correct format
                pass
            elif "fullName" in spouseData:
                # Convert fullName to name components
                name_components = self._parse_name(spouseData.pop("fullName"))
                spouseData["name"] = name_components.dict()
            
            # Remove any legacy name fields
            for field in ["fullName"]:
                spouseData.pop(field, None)
            
            user_ref = db.collection('users').document(userId)
            
            # Validate spouse data
            validated_spouse = SpouseProfile(**spouseData)
            
            # Store in spouse subcollection
            spouse_ref = user_ref.collection('spouse').document('current')
            spouse_ref.set(validated_spouse.dict(), merge=True)
            
            return {"success": True, "spouseId": 'current'}
        
        except Exception as e:
            print(f"Error adding/updating spouse: {e}")
            raise e

    def addChild(self, userId: str, childData: dict) -> dict:
        """Add a new child to the profile"""
        try:
            # Handle name components if provided
            if "name" in childData:
                # Name components are already in the correct format
                pass
            elif "fullName" in childData:
                # Convert fullName to name components
                name_components = self._parse_name(childData.pop("fullName"))
                childData["name"] = name_components.dict()
            
            # Remove any legacy name fields
            for field in ["fullName"]:
                childData.pop(field, None)
            
            # Validate child data
            validated_child = ChildProfile(**childData)
            
            user_ref = db.collection('users').document(userId)
            
            # Create new child document
            child_ref = user_ref.collection('children').document()
            child_ref.set(validated_child.dict())
            
            # Update children count
            self.updateChildrenCount(userId)
            
            return {"success": True, "childId": child_ref.id}
        
        except Exception as e:
            print(f"Error adding child: {e}")
            raise e

    def updateChild(self, userId: str, childId: str, childData: dict) -> dict:
        """Update a specific child's information"""
        try:
            # Handle name components if provided
            if "name" in childData:
                # Name components are already in the correct format
                pass
            elif "fullName" in childData:
                # Convert fullName to name components
                name_components = self._parse_name(childData.pop("fullName"))
                childData["name"] = name_components.dict()
            
            # Remove any legacy name fields
            for field in ["fullName"]:
                childData.pop(field, None)
            
            child_ref = db.collection('users').document(userId).collection('children').document(childId)
            
            # Check if child exists
            current_data = child_ref.get()
            if not current_data.exists:
                return {"success": False, "error": "Child not found"}
            
            # Validate updated data
            updated_data = {**current_data.to_dict(), **childData}
            validated_child = ChildProfile(**updated_data)
            
            # Update child data
            child_ref.set(validated_child.dict(), merge=True)
            
            return {"success": True}
        
        except Exception as e:
            print(f"Error updating child: {e}")
            raise e

    def updateChildrenCount(self, userId: str) -> None:
        """Update children count based on actual documents"""
        try:
            user_ref = db.collection('users').document(userId)
            children_count = len(list(user_ref.collection('children').get()))
            user_ref.set({"childrenCount": children_count}, merge=True)
        except Exception as e:
            print(f"Error updating children count: {e}")
            raise e

    def getProfileCompletionStatus(self, userId: str) -> dict:
        """Check what parts of profile are complete/incomplete"""
        try:
            profile = self.getUserProfile(userId)
            
            if not profile["exists"]:
                return {
                    "isComplete": False,
                    "missingFields": ["profile"]
                }
            
            missing_fields = []
            
            # Check user profile fields
            if "name" not in profile["profile"]:
                missing_fields.append("name")
            else:
                name = profile["profile"]["name"]
                if not name.get("firstName"):
                    missing_fields.append("firstName")
                if not name.get("lastName"):
                    missing_fields.append("lastName")
            
            if not profile["profile"].get("dateOfBirth"):
                missing_fields.append("dateOfBirth")
            if not profile["profile"].get("address"):
                missing_fields.append("address")
            
            # We don't consider spouse required, but if exists, validate structure
            if profile["spouse"]:
                if "name" not in profile["spouse"]:
                    missing_fields.append("spouse_name")
                else:
                    spouse_name = profile["spouse"]["name"]
                    if not spouse_name.get("firstName"):
                        missing_fields.append("spouse_firstName")
                    if not spouse_name.get("lastName"):
                        missing_fields.append("spouse_lastName")
                if not profile["spouse"].get("dateOfBirth"):
                    missing_fields.append("spouse_dateOfBirth")
            
            # We don't consider children required, but if they exist, check for completeness
            if profile["children"]:
                for i, child in enumerate(profile["children"]):
                    if "name" not in child:
                        missing_fields.append(f"child_{i+1}_name")
                    else:
                        child_name = child["name"]
                        if not child_name.get("firstName"):
                            missing_fields.append(f"child_{i+1}_firstName")
                        if not child_name.get("lastName"):
                            missing_fields.append(f"child_{i+1}_lastName")
                    if not child.get("dateOfBirth"):
                        missing_fields.append(f"child_{i+1}_dateOfBirth")
            
            return {
                "isComplete": len(missing_fields) == 0,
                "missingFields": missing_fields
            }
        
        except Exception as e:
            print(f"Error checking profile completion: {e}")
            raise e

    def updateProfileCompletionStatus(self, userId: str) -> dict:
        """Update the profileComplete flag based on current data"""
        try:
            completion_status = self.getProfileCompletionStatus(userId)
            user_ref = db.collection('users').document(userId)
            user_ref.set({"profileComplete": completion_status["isComplete"]}, merge=True)
            
            return completion_status
        
        except Exception as e:
            print(f"Error updating profile completion status: {e}")
            raise e

# Create and export the profile service instance
profile_service = ProfileService()