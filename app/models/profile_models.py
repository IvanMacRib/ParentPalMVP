from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class NameComponents(BaseModel):
    firstName: str
    middleName: Optional[str] = None
    lastName: str

    @validator('firstName', 'lastName')
    def validate_name_parts(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Name parts cannot be empty")
        return v.strip()

class PersonProfile(BaseModel):
    name: NameComponents
    dateOfBirth: Optional[str] = None  # Format: MM/DD/YYYY

    @validator('dateOfBirth')
    def validate_date_format(cls, v):
        if v:
            try:
                # Validate MM/DD/YYYY format
                if not re.match(r"^\d{2}/\d{2}/\d{4}$", v):
                    raise ValueError("Date must be in MM/DD/YYYY format")
                
                # Validate reasonable date
                month, day, year = map(int, v.split('/'))
                if not (1 <= month <= 12 and 1 <= day <= 31):
                    raise ValueError("Invalid month or day")
                
                # Check if date is in the past
                today = datetime.today()
                dob = datetime(year, month, day)
                if dob > today:
                    raise ValueError("Date of birth cannot be in the future")
                
                # Check reasonable age (e.g., not over 120 years)
                age = today.year - dob.year - ((today.month, today.day) < (month, day))
                if age > 120:
                    raise ValueError("Age exceeds reasonable limit")
                
            except ValueError as e:
                raise ValueError(f"Date validation error: {str(e)}")
        return v
    
class UserProfile(PersonProfile):
    address: str
    profileCreatedAt: datetime = Field(default_factory=datetime.now)
    profileUpdatedAt: datetime = Field(default_factory=datetime.now)
    profileComplete: bool = False

    @validator('address')
    def validate_address(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Address cannot be empty")
        # Basic check for address components
        parts = v.strip().split(',')
        if len(parts) < 2:
            raise ValueError("Address must include at least street and city, separated by commas")
        return v.strip()

class SpouseProfile(PersonProfile):
    pass

class ChildProfile(PersonProfile):
    interests: Optional[List[str]] = Field(default_factory=list)
    medicalConsiderations: Optional[List[str]] = Field(default_factory=list)
    
    @validator('dateOfBirth')
    def validate_child_age(cls, v):
        if v:
            try:
                month, day, year = map(int, v.split('/'))
                today = datetime.today()
                dob = datetime(year, month, day)
                
                # Check if child is under 18
                age = today.year - dob.year - ((today.month, today.day) < (month, day))
                if age >= 18:
                    raise ValueError("Child's age must be under 18")
                
            except ValueError as e:
                if "Child's age" in str(e):
                    raise ValueError(str(e))
                # Otherwise, let the first validator handle format errors
        return v 