import requests
import json

# Test case: Employee only available on weekdays 9-17, but shift is on weekend
# This should be infeasible due to availability constraint
availability_test_config = {
    "employees": [
        {
            "id": "emp-1",
            "name": "John Doe",
            "role": "Manager",
            "skills": ["Leadership"],
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
                },
                {
                    "dayOfWeek": 2,  # Wednesday
                    "startTime": "09:00",
                    "endTime": "17:00"
                },
                {
                    "dayOfWeek": 3,  # Thursday
                    "startTime": "09:00",
                    "endTime": "17:00"
                },
                {
                    "dayOfWeek": 4,  # Friday
                    "startTime": "09:00",
                    "endTime": "17:00"
                }
            ],
            "preferences": [],
            "email": "john@example.com"
        }
    ],
    "shiftTypes": [
        {
            "id": "shift-1",
            "name": "Weekend Shift",
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
        "startDate": "2024-01-06T00:00:00.000Z",  # Saturday
        "endDate": "2024-01-06T00:00:00.000Z",    # Saturday
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

print("Testing availability constraint - Employee only available weekdays, shift on Saturday")
print("Expected: Infeasible (no solution)")
print()

# Test the API
try:
    response = requests.post(
        "http://localhost:8000/schedule",
        json=availability_test_config,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if result.get("shifts"):
        print("✅ FEASIBLE - Schedule found:")
        print(f"   Coverage: {result['analytics']['shiftCoveragePercentage']}%")
    else:
        print("❌ INFEASIBLE - No schedule found")
        if result.get("violations"):
            print(f"   Reason: {result['violations'][0]['description']}")
    
except Exception as e:
    print(f"Error: {e}")