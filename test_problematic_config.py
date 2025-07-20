#!/usr/bin/env python3

import requests
import json

# The problematic config from the user
problematic_config = {
  "employees": [
    {
      "id": "emp-1752850515804-0",
      "name": "Employee_1",
      "role": "Security",
      "skills": [
        "Experienced",
        "Fast"
      ],
      "maxHoursPerWeek": 40,
      "availability": [],
      "preferences": [
        "Flexible"
      ],
      "email": ""
    },
    {
      "id": "emp-1752850515805-1",
      "name": "Employee_2",
      "role": "Cleaner",
      "skills": [
        "Bilingual",
        "Team Player",
        "Experienced"
      ],
      "maxHoursPerWeek": 30,
      "availability": [],
      "preferences": [
        "Prefer Weekends"
      ],
      "email": ""
    }
  ],
  "shiftTypes": [
    {
      "id": "shift-1752850533377",
      "name": "morn",
      "startTime": "12:00",
      "endTime": "13:00",
      "requiredRoles": [],  # THIS IS THE PROBLEM!
      "duration": 1,
      "isRepeating": True,
      "repeatPattern": "daily",
      "priority": 5
    }
  ],
  "schedulingPeriod": {
    "startDate": "2025-07-13T21:00:00.000Z",
    "endDate": "2025-07-20T20:59:59.999Z",
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
    "maxHoursPerEmployee": 60,
    "maxShiftsPerDay": 3,
    "maxNightShiftsPerWeek": 7,
    "minHoursBetweenShifts": 4,
    "preferFixedTeams": False,
    "prioritizeFairness": 0.9
  },
  "preferences": {
    "respectEmployeePreferences": True,
    "minimizeNightShifts": True,
    "spreadWeekendShiftsFairly": True,
    "minimizeConsecutiveNightShifts": True,
    "preferenceWeight": 0
  }
}

def test_problematic_config():
    """Test the problematic config"""
    try:
        response = requests.post(
            "http://localhost:8000/schedule",
            json=problematic_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("=== PROBLEMATIC CONFIG TEST ===")
            print(f"Total shifts generated: {len(result['shifts'])}")
            
            for i, shift in enumerate(result['shifts']):
                print(f"\nShift {i+1}:")
                print(f"  ID: {shift['id']}")
                print(f"  Date: {shift['date']}")
                print(f"  Time: {shift['startTime']} - {shift['endTime']}")
                print(f"  Assigned employees: {shift['assignedEmployees']}")
                print(f"  Status: {shift['status']}")
                
            print(f"\nConstraint violations: {len(result['violations'])}")
            for violation in result['violations']:
                print(f"  - {violation['type']}: {violation['description']}")
                
            return result
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    test_problematic_config()