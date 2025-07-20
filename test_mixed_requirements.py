#!/usr/bin/env python3

import requests
import json

# Test config with both empty and specific role requirements
mixed_config = {
  "employees": [
    {
      "id": "manager1",
      "name": "Manager Alice",
      "role": "Manager",
      "skills": ["Leadership"],
      "maxHoursPerWeek": 40,
      "availability": [],
      "preferences": [],
      "email": ""
    },
    {
      "id": "cashier1",
      "name": "Cashier Bob",
      "role": "Cashier",
      "skills": ["Customer Service"],
      "maxHoursPerWeek": 40,
      "availability": [],
      "preferences": [],
      "email": ""
    }
  ],
  "shiftTypes": [
    {
      "id": "flexible-shift",
      "name": "Flexible Shift",
      "startTime": "09:00",
      "endTime": "10:00",
      "requiredRoles": [],  # No specific requirements
      "duration": 1,
      "isRepeating": True,
      "repeatPattern": "daily",
      "priority": 5
    },
    {
      "id": "manager-shift",
      "name": "Manager Shift",
      "startTime": "14:00",
      "endTime": "15:00",
      "requiredRoles": [{"role": "Manager", "count": 1}],  # Specific requirement
      "duration": 1,
      "isRepeating": True,
      "repeatPattern": "daily",
      "priority": 5
    }
  ],
  "schedulingPeriod": {
    "startDate": "2025-01-15T00:00:00Z",
    "endDate": "2025-01-16T23:59:59Z",
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
    "maxShiftsPerDay": 3,
    "maxNightShiftsPerWeek": 7,
    "minHoursBetweenShifts": 4,
    "preferFixedTeams": False,
    "prioritizeFairness": 0.5
  },
  "preferences": {
    "respectEmployeePreferences": True,
    "minimizeNightShifts": True,
    "spreadWeekendShiftsFairly": True,
    "minimizeConsecutiveNightShifts": True,
    "preferenceWeight": 0.5
  }
}

def test_mixed_requirements():
    """Test config with both empty and specific role requirements"""
    try:
        response = requests.post(
            "http://localhost:8000/schedule",
            json=mixed_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("=== MIXED REQUIREMENTS TEST ===")
            print(f"Total shifts generated: {len(result['shifts'])}")
            
            for i, shift in enumerate(result['shifts']):
                print(f"\nShift {i+1}:")
                print(f"  ID: {shift['id']}")
                print(f"  Date: {shift['date']}")
                print(f"  Time: {shift['startTime']} - {shift['endTime']}")
                print(f"  Assigned employees: {shift['assignedEmployees']}")
                print(f"  Status: {shift['status']}")
                
            print(f"\nEmployee utilization:")
            for util in result['analytics']['employeeUtilization']:
                print(f"  {util['employeeId']}: {util['shiftsAssigned']} shifts, {util['totalHours']} hours")
                
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
    test_mixed_requirements()