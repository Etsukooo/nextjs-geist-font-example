from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import os


def emr_file_upload_path(instance, filename):
    """Generate upload path for EMR files"""
    return f'emr_files/{instance.patient.username}/{filename}'


class EMRRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emr_requests',
        limit_choices_to={'role': 'PATIENT'}
    )
    requested_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    request_reason = models.TextField(help_text="Reason for requesting EMR access")
    
    # Fields for approval/denial
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_emr_requests',
        limit_choices_to={'role__in': ['DOCTOR', 'ADMIN']}
    )
    reviewed_on = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-requested_on']
    
    def __str__(self):
        return f"EMR Request by {self.patient.username} - {self.status}"
    
    def clean(self):
        if self.patient and not self.patient.is_patient:
            raise ValidationError("EMR requests can only be made by patients.")
        
        if self.reviewed_by and not (self.reviewed_by.is_doctor or self.reviewed_by.is_admin):
            raise ValidationError("EMR requests can only be reviewed by doctors or admins.")


class EMRFile(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emr_files',
        limit_choices_to={'role': 'PATIENT'}
    )
    file = models.FileField(upload_to=emr_file_upload_path)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_emr_files',
        limit_choices_to={'role__in': ['DOCTOR', 'ADMIN']}
    )
    uploaded_on = models.DateTimeField(auto_now_add=True)
    is_accessible = models.BooleanField(default=False, help_text="Whether patient can access this file")
    
    class Meta:
        ordering = ['-uploaded_on']
    
    def __str__(self):
        return f"EMR File: {self.file_name} for {self.patient.username}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = os.path.basename(self.file.name)
            # Get file extension
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lower()
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.patient and not self.patient.is_patient:
            raise ValidationError("EMR files can only be associated with patients.")
        
        if self.uploaded_by and not (self.uploaded_by.is_doctor or self.uploaded_by.is_admin):
            raise ValidationError("EMR files can only be uploaded by doctors or admins.")
