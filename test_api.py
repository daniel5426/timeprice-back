import requests
import json

# Minimal test data: 1 employee, 1 shift, 1 required role
minimal_test_config = {
    "employees": [
        {
            "id": "emp-1",
            "name": "John Doe",
            "role": "Manager",
            "skills": ["Leadership"],
            "maxHoursPerWeek": 40,
            "availability": [],
            "preferences": [],
            "email": "john@example.com"
        }
    ],
    "shiftTypes": [
        {
            "id": "shift-1",
            "name": "Morning",
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
        "startDate": "2024-01-01T00:00:00.000Z",
        "endDate": "2024-01-01T00:00:00.000Z",
        "daysOff": [],
        "holidays": [],
        "minRestTimeBetweenShifts": 8,
        "weekendRules": {
            "rotateWeekends": False,
            "avoidBackToBack": False,
            "maxWeekendsPerMonth": 2
        }
    },
    "constraints": {
        "maxHoursPerEmployee": 40,
        "maxShiftsPerDay": 1,
        "maxNightShiftsPerWeek": 3,
        "minHoursBetweenShifts": 8,
        "preferFixedTeams": False,
        "prioritizeFairness": 0.7
    },
    "preferences": {
        "respectEmployeePreferences": False,
        "minimizeNightShifts": False,
        "spreadWeekendShiftsFairly": False,
        "minimizeConsecutiveNightShifts": False,
        "preferenceWeight": 0.0
    }
}

# Test the API
try:
    response = requests.post(
        "http://localhost:8000/schedule",
        json=minimal_test_config,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"Error: {e}") 