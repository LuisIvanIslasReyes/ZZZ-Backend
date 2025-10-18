"""
Department models
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Department(models.Model):
    """Department model"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    
    # Hierarchy
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments'
    )
    
    # Management
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    
    # Employees (many-to-many through Employee profile)
    employees = models.ManyToManyField(
        User,
        through='DepartmentMembership',
        related_name='departments'
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    
    # Contact info
    location = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def employee_count(self):
        return self.employees.count()
    
    def get_all_employees(self, include_sub_departments=True):
        """Get all employees including from sub-departments"""
        employees = self.employees.all()
        
        if include_sub_departments:
            for sub_dept in self.sub_departments.all():
                employees = employees.union(sub_dept.get_all_employees())
        
        return employees


class DepartmentMembership(models.Model):
    """Through model for department-employee relationship"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    # Role in department
    position = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=True)  # Primary department for employee
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'department']
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department.name}"


class WorkShift(models.Model):
    """Work shift model"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Time settings
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Days of week (JSON array of day numbers: 0=Monday, 6=Sunday)
    work_days = models.JSONField(default=list, help_text="Array of work day numbers (0-6)")
    
    # Department association
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='work_shifts'
    )
    
    # Employees in this shift
    employees = models.ManyToManyField(
        User,
        through='ShiftAssignment',
        related_name='work_shifts'
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    break_duration_minutes = models.PositiveIntegerField(default=60)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['department', 'start_time']
        unique_together = ['department', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
    
    @property
    def duration_hours(self):
        """Calculate shift duration in hours"""
        from datetime import datetime, timedelta
        
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # Handle overnight shifts
        if end < start:
            end += timedelta(days=1)
        
        duration = end - start
        return duration.total_seconds() / 3600


class ShiftAssignment(models.Model):
    """Through model for shift-employee assignment"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE)
    
    # Assignment details
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'work_shift', 'start_date']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.work_shift.name}"