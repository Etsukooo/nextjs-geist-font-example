from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_appointments',
        limit_choices_to={'role': 'PATIENT'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_appointments',
        limit_choices_to={'role': 'DOCTOR'}
    )
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True, null=True)
    reason_for_visit = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
        unique_together = ['doctor', 'scheduled_time']
    
    def __str__(self):
        return f"{self.patient.username} with Dr. {self.doctor.username} on {self.scheduled_time}"
    
    def clean(self):
        # Validate that appointment is not in the past
        if self.scheduled_time and self.scheduled_time < timezone.now():
            raise ValidationError("Cannot schedule appointments in the past.")
        
        # Validate that patient and doctor have correct roles
        if self.patient and not self.patient.is_patient:
            raise ValidationError("Patient must have PATIENT role.")
        
        if self.doctor and not self.doctor.is_doctor:
            raise ValidationError("Doctor must have DOCTOR role.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
