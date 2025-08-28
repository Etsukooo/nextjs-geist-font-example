from rest_framework import serializers
from django.utils import timezone
from .models import Appointment
from users.serializers import UserProfileSerializer, DoctorListSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    patient_details = UserProfileSerializer(source='patient', read_only=True)
    doctor_details = DoctorListSerializer(source='doctor', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'scheduled_time', 'status', 
                 'notes', 'reason_for_visit', 'created_at', 'updated_at',
                 'patient_details', 'doctor_details']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_scheduled_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Cannot schedule appointments in the past.")
        return value
    
    def validate(self, attrs):
        # Check for conflicting appointments
        doctor = attrs.get('doctor')
        scheduled_time = attrs.get('scheduled_time')
        
        if doctor and scheduled_time:
            # Check if doctor already has an appointment at this time
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                scheduled_time=scheduled_time,
                status='SCHEDULED'
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_appointment.exists():
                raise serializers.ValidationError(
                    "Doctor already has an appointment at this time."
                )
        
        return attrs


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['doctor', 'scheduled_time', 'reason_for_visit', 'notes']
    
    def validate_scheduled_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Cannot schedule appointments in the past.")
        return value
    
    def create(self, validated_data):
        # Set the patient to the current user
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['scheduled_time', 'status', 'notes', 'reason_for_visit']
    
    def validate_scheduled_time(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Cannot reschedule appointments to the past.")
        return value
