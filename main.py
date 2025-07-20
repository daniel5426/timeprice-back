from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Optional, Dict, Any, Literal
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AvailabilitySlot(BaseModel):
    dayOfWeek: int
    startTime: str
    endTime: str

class Employee(BaseModel):
    id: str
    name: str
    role: str
    skills: List[str]
    maxHoursPerWeek: int
    availability: List[AvailabilitySlot]
    preferences: List[str]
    email: Optional[str] = None

class RequiredRole(BaseModel):
    role: str
    count: int

class ShiftType(BaseModel):
    id: str
    name: str
    startTime: str
    endTime: str
    requiredRoles: List[RequiredRole]
    duration: float
    isRepeating: bool
    repeatPattern: Literal['daily', 'weekly', 'custom']
    priority: int

class WeekendRules(BaseModel):
    rotateWeekends: bool = False
    avoidBackToBack: bool = False
    maxWeekendsPerMonth: int = 2

class SchedulingPeriod(BaseModel):
    startDate: str
    endDate: str
    daysOff: List[str] = []
    holidays: List[str] = []
    minRestTimeBetweenShifts: int = 12
    weekendRules: WeekendRules = WeekendRules()

    @field_validator('startDate', 'endDate')
    @classmethod
    def parse_dates(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @field_validator('daysOff', 'holidays')
    @classmethod
    def parse_date_lists(cls, v):
        if isinstance(v, list):
            return [datetime.fromisoformat(date.replace('Z', '+00:00')) if isinstance(date, str) else date for date in v]
        return v

class Constraints(BaseModel):
    maxHoursPerEmployee: int
    maxShiftsPerDay: int
    maxNightShiftsPerWeek: int
    minHoursBetweenShifts: int
    preferFixedTeams: bool
    prioritizeFairness: float

class Preferences(BaseModel):
    respectEmployeePreferences: bool
    minimizeNightShifts: bool
    spreadWeekendShiftsFairly: bool
    minimizeConsecutiveNightShifts: bool
    preferenceWeight: float

class SchedulingConfig(BaseModel):
    employees: List[Employee]
    shiftTypes: List[ShiftType]
    schedulingPeriod: SchedulingPeriod
    constraints: Constraints
    preferences: Preferences

class GeneratedShift(BaseModel):
    id: str
    shiftTypeId: str
    date: datetime
    startTime: str
    endTime: str
    assignedEmployees: List[str]
    status: Literal['confirmed', 'pending', 'conflict']

class EmployeeUtilization(BaseModel):
    employeeId: str
    totalHours: float
    utilizationPercentage: float
    shiftsAssigned: int
    preferencesRespected: int

class ScheduleAnalytics(BaseModel):
    shiftCoveragePercentage: float
    preferenceSatisfactionScore: float
    fairnessMetric: float
    totalHoursScheduled: float
    employeeUtilization: List[EmployeeUtilization]

class ConstraintViolation(BaseModel):
    type: Literal['hard', 'soft']
    description: str
    severity: int
    affectedEmployees: List[str]
    affectedShifts: List[str]

class ScheduleResult(BaseModel):
    shifts: List[GeneratedShift]
    analytics: ScheduleAnalytics
    violations: List[ConstraintViolation]

def parse_time(time_str: str) -> int:
    """Convert time string (HH:MM) to minutes since midnight"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def is_night_shift(start_time: str, end_time: str) -> bool:
    """Determine if a shift is a night shift (10 PM - 6 AM)"""
    start_minutes = parse_time(start_time)
    end_minutes = parse_time(end_time)
    
    # Night shift: 22:00 (1320 minutes) to 06:00 (360 minutes)
    night_start = 22 * 60  # 10 PM
    night_end = 6 * 60     # 6 AM
    
    if start_minutes >= night_start or end_minutes <= night_end:
        return True
    return False

def is_weekend(date: datetime) -> bool:
    """Check if date is weekend (Saturday=5, Sunday=6)"""
    return date.weekday() >= 5

def optimize_schedule(config: SchedulingConfig) -> ScheduleResult:
    """Main optimization function using Google OR-Tools"""
    # Ensure startDate and endDate are datetime objects
    if isinstance(config.schedulingPeriod.startDate, str):
        start_date = datetime.fromisoformat(config.schedulingPeriod.startDate.replace('Z', '+00:00'))
    else:
        start_date = config.schedulingPeriod.startDate
    if isinstance(config.schedulingPeriod.endDate, str):
        end_date = datetime.fromisoformat(config.schedulingPeriod.endDate.replace('Z', '+00:00'))
    else:
        end_date = config.schedulingPeriod.endDate
    holidays = [datetime.fromisoformat(d.replace('Z', '+00:00')) if isinstance(d, str) else d for d in config.schedulingPeriod.holidays]
    days_off = [datetime.fromisoformat(d.replace('Z', '+00:00')) if isinstance(d, str) else d for d in config.schedulingPeriod.daysOff]

    # Create the model
    model = cp_model.CpModel()
    
    # Generate all shifts for the scheduling period
    shifts = []
    current_date = start_date
    shift_id_counter = 0
    
    while current_date <= end_date:
        # Skip holidays and days off
        if any(current_date.date() == h.date() for h in holidays) or any(current_date.date() == d.date() for d in days_off):
            current_date += timedelta(days=1)
            continue
        for shift_type in config.shiftTypes:
            if shift_type.isRepeating:
                shifts.append({
                    'id': f"shift-{shift_id_counter}",
                    'shiftTypeId': shift_type.id,
                    'date': current_date,
                    'startTime': shift_type.startTime,
                    'endTime': shift_type.endTime,
                    'duration': int(shift_type.duration * 60),  # Convert to minutes for integer constraints
                    'requiredRoles': shift_type.requiredRoles,
                    'isNightShift': is_night_shift(shift_type.startTime, shift_type.endTime),
                    'isWeekend': is_weekend(current_date)
                })
                shift_id_counter += 1
        current_date += timedelta(days=1)
    
    def to_serializable(val):
        if isinstance(val, datetime):
            return val.isoformat()
        if hasattr(val, 'dict'):
            return val.dict()
        if isinstance(val, list):
            return [to_serializable(v) for v in val]
        return val

    print(f"Generated shifts: {json.dumps([{k: to_serializable(v) for k, v in s.items()} for s in shifts], indent=2)}")
    
    # Create variables: employee_shift[employee_id][shift_id] = 1 if assigned
    employee_shift = {}
    for employee in config.employees:
        employee_shift[employee.id] = {}
        for shift in shifts:
            employee_shift[employee.id][shift['id']] = model.NewBoolVar(f'employee_{employee.id}_shift_{shift["id"]}')
    
    # Hard Constraints
    
    # 0. Employee availability constraint - employees can only work during their available times
    for employee in config.employees:
        if employee.availability:  # Only apply if availability is specified
            for shift in shifts:
                shift_day_of_week = shift['date'].weekday()  # Monday=0, Sunday=6
                shift_start_minutes = parse_time(shift['startTime'])
                shift_end_minutes = parse_time(shift['endTime'])
                
                # Check if employee is available for this shift
                is_available = False
                for availability_slot in employee.availability:
                    slot_day = availability_slot.dayOfWeek
                    slot_start = parse_time(availability_slot.startTime)
                    slot_end = parse_time(availability_slot.endTime)
                    
                    # Check if shift day matches and shift time overlaps with availability
                    if (shift_day_of_week == slot_day and
                        shift_start_minutes >= slot_start and
                        shift_end_minutes <= slot_end):
                        is_available = True
                        break
                
                # If not available, prevent assignment
                if not is_available:
                    model.Add(employee_shift[employee.id][shift['id']] == 0)
    
    # 1. Each shift must have the required number of employees per role
    for shift in shifts:
        if shift['requiredRoles']:
            # Shift has specific role requirements
            for required_role in shift['requiredRoles']:
                role_employees = [emp.id for emp in config.employees if emp.role == required_role.role]
                if role_employees:
                    assigned_count = sum(employee_shift[emp_id][shift['id']] for emp_id in role_employees)
                    model.Add(assigned_count == required_role.count)
        else:
            # Shift has no specific role requirements - assign at least 1 employee from any role
            all_employees = [emp.id for emp in config.employees]
            if all_employees:
                assigned_count = sum(employee_shift[emp_id][shift['id']] for emp_id in all_employees)
                model.Add(assigned_count >= 1)  # At least one employee must be assigned
    
    # 2. Employee can only work one shift per day
    for employee in config.employees:
        for shift in shifts:
            # Find all other shifts on the same day
            same_day_shifts = [s for s in shifts if s['date'] == shift['date'] and s['id'] != shift['id']]
            for other_shift in same_day_shifts:
                model.Add(employee_shift[employee.id][shift['id']] + 
                         employee_shift[employee.id][other_shift['id']] <= 1)
    
    # 3. Maximum hours per employee per week (convert to minutes)
    max_minutes_per_week = config.constraints.maxHoursPerEmployee * 60
    for employee in config.employees:
        # Group shifts by week properly based on dates
        shifts_by_week = {}
        for shift in shifts:
            # Get the Monday of the week for this shift (ISO week)
            week_start = shift['date'] - timedelta(days=shift['date'].weekday())
            week_key = week_start.strftime('%Y-%W')
            if week_key not in shifts_by_week:
                shifts_by_week[week_key] = []
            shifts_by_week[week_key].append(shift)
        
        # Apply weekly hour constraints for each week
        for week_shifts in shifts_by_week.values():
            total_minutes = sum(employee_shift[employee.id][shift['id']] * shift['duration']
                              for shift in week_shifts)
            model.Add(total_minutes <= max_minutes_per_week)
    
    # 4. Minimum rest time between shifts
    for employee in config.employees:
        for i, shift1 in enumerate(shifts):
            for j, shift2 in enumerate(shifts):
                if i != j:
                    # Check if shifts are consecutive days
                    if (shift2['date'] - shift1['date']).days == 1:
                        # If employee works both shifts, ensure minimum rest
                        end_time1 = parse_time(shift1['endTime'])
                        start_time2 = parse_time(shift2['startTime'])
                        rest_hours = (24 * 60 - end_time1 + start_time2) / 60
                        
                        if rest_hours < config.constraints.minHoursBetweenShifts:
                            model.Add(employee_shift[employee.id][shift1['id']] + 
                                    employee_shift[employee.id][shift2['id']] <= 1)
    
    # 5. Maximum night shifts per week
    for employee in config.employees:
        # Use the same weekly grouping as above
        shifts_by_week = {}
        for shift in shifts:
            week_start = shift['date'] - timedelta(days=shift['date'].weekday())
            week_key = week_start.strftime('%Y-%W')
            if week_key not in shifts_by_week:
                shifts_by_week[week_key] = []
            shifts_by_week[week_key].append(shift)
        
        # Apply night shift constraints for each week
        for week_shifts in shifts_by_week.values():
            night_shifts = [s for s in week_shifts if s['isNightShift']]
            night_shift_count = sum(employee_shift[employee.id][shift['id']]
                                  for shift in night_shifts)
            model.Add(night_shift_count <= config.constraints.maxNightShiftsPerWeek)
    
    # 6. Fairness constraint - limit maximum shifts per employee to prevent one employee from getting all shifts
    if config.constraints.prioritizeFairness > 0.5:  # Only apply when fairness is highly prioritized
        total_shifts = len(shifts)
        max_shifts_per_employee = max(1, total_shifts // len(config.employees) + 1)  # Allow some flexibility
        
        for employee in config.employees:
            employee_total_shifts = sum(employee_shift[employee.id][shift['id']] 
                                      for shift in shifts)
            model.Add(employee_total_shifts <= max_shifts_per_employee)
    
    # Soft Constraints (objectives)
    objectives = []
    
    # 1. Fairness objective - distribute shifts evenly among employees
    if config.constraints.prioritizeFairness > 0:
        # Calculate total shifts that need to be assigned
        total_shifts_needed = len(shifts)
        
        # Calculate ideal shifts per employee (fair distribution) - use integer arithmetic
        ideal_shifts_per_employee = total_shifts_needed // len(config.employees) if config.employees else 0
        
        # Create fairness penalty for each employee
        fairness_penalty = 0
        for employee in config.employees:
            employee_total_shifts = sum(employee_shift[employee.id][shift['id']] 
                                      for shift in shifts)
            # Penalize deviation from ideal distribution using integer arithmetic
            deviation = model.NewIntVar(0, total_shifts_needed, f'deviation_{employee.id}')
            model.Add(deviation >= employee_total_shifts - ideal_shifts_per_employee)
            model.Add(deviation >= ideal_shifts_per_employee - employee_total_shifts)
            fairness_penalty += deviation
        
        # Add fairness objective with weight (convert to integer)
        objectives.append(fairness_penalty * int(config.constraints.prioritizeFairness * 100))
    
    # 2. Minimize night shifts (if preference enabled)
    if config.preferences.minimizeNightShifts:
        night_shift_penalty = sum(employee_shift[emp.id][shift['id']] 
                                for emp in config.employees 
                                for shift in shifts if shift['isNightShift'])
        objectives.append(night_shift_penalty)
    
    # 3. Fair weekend distribution
    if config.preferences.spreadWeekendShiftsFairly:
        weekend_shifts = [s for s in shifts if s['isWeekend']]
        for employee in config.employees:
            weekend_count = sum(employee_shift[employee.id][shift['id']] 
                              for shift in weekend_shifts)
            # Penalize if employee has too many weekend shifts
            model.Add(weekend_count <= 2)  # Max 2 weekend shifts per period
    
    # Set objective function to minimize the sum of all objectives
    if objectives:
        model.Minimize(sum(objectives))
    
    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(f"Solver status: {status}")
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Extract solution
        generated_shifts = []
        for shift in shifts:
            assigned_employees = []
            for employee in config.employees:
                if solver.Value(employee_shift[employee.id][shift['id']]) == 1:
                    assigned_employees.append(employee.id)
            
            generated_shifts.append(GeneratedShift(
                id=shift['id'],
                shiftTypeId=shift['shiftTypeId'],
                date=shift['date'],
                startTime=shift['startTime'],
                endTime=shift['endTime'],
                assignedEmployees=assigned_employees,
                status='confirmed' if assigned_employees else 'pending'
            ))
        
        # Calculate analytics
        employee_utilization = []
        total_hours = 0
        
        for employee in config.employees:
            employee_shifts = [s for s in generated_shifts if employee.id in s.assignedEmployees]
            total_employee_hours = 0
            
            for shift in employee_shifts:
                # Find the corresponding shift type to get duration
                shift_type = next((st for st in config.shiftTypes if st.id == shift.shiftTypeId), None)
                if shift_type:
                    total_employee_hours += shift_type.duration
            
            total_hours += total_employee_hours
            
            employee_utilization.append(EmployeeUtilization(
                employeeId=employee.id,
                totalHours=total_employee_hours,
                utilizationPercentage=(total_employee_hours / employee.maxHoursPerWeek) * 100,
                shiftsAssigned=len(employee_shifts),
                preferencesRespected=85  # Placeholder
            ))
        
        # Calculate coverage percentage
        filled_shifts = len([s for s in generated_shifts if s.assignedEmployees])
        coverage_percentage = (filled_shifts / len(generated_shifts)) * 100 if generated_shifts else 0
        
        analytics = ScheduleAnalytics(
            shiftCoveragePercentage=coverage_percentage,
            preferenceSatisfactionScore=85.0,  # Placeholder
            fairnessMetric=90.0,  # Placeholder
            totalHoursScheduled=total_hours,
            employeeUtilization=employee_utilization
        )
        
        return ScheduleResult(
            shifts=generated_shifts,
            analytics=analytics,
            violations=[]
        )
    else:
        print(f"No solution found")
        # Return empty result if no solution found
        return ScheduleResult(
            shifts=[],
            analytics=ScheduleAnalytics(
                shiftCoveragePercentage=0,
                preferenceSatisfactionScore=0,
                fairnessMetric=0,
                totalHoursScheduled=0,
                employeeUtilization=[]
            ),
            violations=[ConstraintViolation(
                type="hard",
                description="No feasible solution found with current constraints",
                severity=10,
                affectedEmployees=[],
                affectedShifts=[]
            )]
        )

@app.post("/test")
async def test_endpoint(request: Request):
    """Test endpoint to verify API is working"""
    try:
        body = await request.json()
        return {"message": "Test successful", "received": body}
    except Exception as e:
        return {"error": str(e)}

@app.post("/schedule")
async def schedule_endpoint(request: Request):
    """Generate optimized schedule using Google OR-Tools"""
    try:
        # First, get the raw JSON to debug
        raw_body = await request.json()
        print(f"Raw request body: {json.dumps(raw_body, indent=2)}")
        
        # Try to parse with Pydantic
        try:
            config = SchedulingConfig(**raw_body)
        except ValidationError as e:
            print(f"Validation error: {e.json()}")
            raise HTTPException(status_code=422, detail=f"Validation error: {e.json()}")
        
        result = optimize_schedule(config)
        return result.dict()
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Shift Scheduler API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 