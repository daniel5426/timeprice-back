#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

# Test data that matches frontend format
test_config = {
    "employees": [
        {
            "id": "emp1",
            "name": "John Manager",
            "role": "Manager",
            "skills": ["Leadership", "Customer Service"],
            "maxHoursPerWeek": 40,
            "availability": [
                {
                    "dayOfWeek": 0,  # Monday
                    "startTime": "09:00",
                    "endTime": "17:00"
                },
                {
                    "dayOfWeek": 1,  # Tuesday
                    "startTime": "09:00",
                    "endTime": "17:00"
                }
            ],
            "preferences": ["Morning shifts"],
            "email": "john@example.com"
        }
    ],
    "shiftTypes": [
        {
            "id": "morning-shift",
            "name": "Morning Shift",
            "startTime": "09:00",
            "endTime": "17:00",
            "requiredRoles": [
                {
                    "role": "Manager",
                    "count": 1
                }
            ],
            "duration": 8.0,
            "isRepeating": True,
            "repeatPattern": "daily",
            "priority": 5
        }
    ],
    "schedulingPeriod": {
        "startDate": "2024-01-15T00:00:00Z",
        "endDate": "2024-01-16T23:59:59Z",
        "daysOff": [],
        "holidays": [],
        "minRestTimeBetweenShifts": 12,
        "weekendRules": {
            "rotateWeekends": True,
            "avoidBackToBack": True,
            "maxWeekendsPerMonth": 2
        }
    },
    "constraints": {
        "maxHoursPerEmployee": 40,
        "maxShiftsPerDay": 1,
        "maxNightShiftsPerWeek": 2,
        "minHoursBetweenShifts": 12,
        "preferFixedTeams": False,
        "prioritizeFairness": 0.8
    },
    "preferences": {
        "respectEmployeePreferences": True,
        "minimizeNightShifts": True,
        "spreadWeekendShiftsFairly": True,
        "minimizeConsecutiveNightShifts": True,
        "preferenceWeight": 0.7
    }
}

def test_api():
    """Test the API with frontend-compatible data"""
    try:
        # Test the root endpoint
        print("Testing root endpoint...")
        response = requests.get("http://localhost:8000/")
        print(f"Root response: {response.json()}")
        
        # Test the schedule endpoint
        print("\nTesting schedule endpoint...")
        response = requests.post(
            "http://localhost:8000/schedule",
            json=test_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful!")
            print(f"Generated {len(result['shifts'])} shifts")
            print(f"Coverage: {result['analytics']['shiftCoveragePercentage']:.1f}%")
            
            # Check if dates are properly formatted
            if result['shifts']:
                first_shift = result['shifts'][0]
                print(f"First shift date: {first_shift['date']} (type: {type(first_shift['date'])})")
                print(f"First shift status: {first_shift['status']}")
                
            return True
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n🎉 Frontend-API integration test passed!")
    else:
        print("\n💥 Frontend-API integration test failed!")