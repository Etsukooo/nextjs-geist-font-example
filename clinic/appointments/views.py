from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment
from .serializers import (
    AppointmentSerializer, 
    AppointmentCreateSerializer, 
    AppointmentUpdateSerializer
)
from users.permissions import IsPatientOwnerOrDoctorOrAdmin, IsDoctorOrAdmin
from users.models import CustomUser


# API Views
class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctorOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Appointment.objects.filter(patient=user)
        elif user.is_doctor:
            return Appointment.objects.filter(doctor=user)
        else:  # Admin
            return Appointment.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsPatientOwnerOrDoctorOrAdmin])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'CANCELLED':
            return Response({'error': 'Appointment is already cancelled'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = 'CANCELLED'
        appointment.save()
        return Response({'message': 'Appointment cancelled successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsDoctorOrAdmin])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != 'SCHEDULED':
            return Response({'error': 'Only scheduled appointments can be completed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = 'COMPLETED'
        appointment.notes = request.data.get('notes', appointment.notes)
        appointment.save()
        return Response({'message': 'Appointment marked as completed'})


# Web Views
@login_required
def appointment_list(request):
    if request.user.is_patient:
        appointments = request.user.patient_appointments.all()
    elif request.user.is_doctor:
        appointments = request.user.doctor_appointments.all()
    else:  # Admin
        appointments = Appointment.objects.all()
    
    context = {
        'appointments': appointments,
        'user_role': request.user.role
    }
    return render(request, 'appointments/appointment_list.html', context)


@login_required
def appointment_create(request):
    if not request.user.is_patient:
        messages.error(request, 'Only patients can book appointments.')
        return redirect('appointment_list')
    
    doctors = CustomUser.objects.filter(role='DOCTOR', is_active=True)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        scheduled_time = request.POST.get('scheduled_time')
        reason_for_visit = request.POST.get('reason_for_visit')
        notes = request.POST.get('notes', '')
        
        try:
            doctor = CustomUser.objects.get(id=doctor_id, role='DOCTOR')
            scheduled_time = timezone.datetime.fromisoformat(scheduled_time.replace('T', ' '))
            
            # Check if time is in the future
            if scheduled_time < timezone.now():
                messages.error(request, 'Cannot schedule appointments in the past.')
                return render(request, 'appointments/appointment_create.html', {'doctors': doctors})
            
            # Check for conflicts
            if Appointment.objects.filter(doctor=doctor, scheduled_time=scheduled_time, status='SCHEDULED').exists():
                messages.error(request, 'Doctor already has an appointment at this time.')
                return render(request, 'appointments/appointment_create.html', {'doctors': doctors})
            
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                scheduled_time=scheduled_time,
                reason_for_visit=reason_for_visit,
                notes=notes
            )
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointment_list')
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
    
    context = {'doctors': doctors}
    return render(request, 'appointments/appointment_create.html', context)


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if request.user.is_patient and appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointment_list')
    elif request.user.is_doctor and appointment.doctor != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointment_list')
    
    context = {'appointment': appointment}
    return render(request, 'appointments/appointment_detail.html', context)


@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if request.user.is_patient and appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointment_list')
    elif request.user.is_doctor and appointment.doctor != request.user and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('appointment_list')
    
    if appointment.status == 'CANCELLED':
        messages.warning(request, 'Appointment is already cancelled.')
        return redirect('appointment_detail', pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointment_list')
    
    context = {'appointment': appointment}
    return render(request, 'appointments/appointment_cancel.html', context)


@login_required
def appointment_reschedule(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Only patients can reschedule their own appointments
    if not request.user.is_patient or appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointment_list')
    
    if appointment.status != 'SCHEDULED':
        messages.error(request, 'Only scheduled appointments can be rescheduled.')
        return redirect('appointment_detail', pk=pk)
    
    if request.method == 'POST':
        new_time = request.POST.get('scheduled_time')
        try:
            new_time = timezone.datetime.fromisoformat(new_time.replace('T', ' '))
            
            if new_time < timezone.now():
                messages.error(request, 'Cannot reschedule to the past.')
                return render(request, 'appointments/appointment_reschedule.html', {'appointment': appointment})
            
            # Check for conflicts
            if Appointment.objects.filter(
                doctor=appointment.doctor, 
                scheduled_time=new_time, 
                status='SCHEDULED'
            ).exclude(id=appointment.id).exists():
                messages.error(request, 'Doctor already has an appointment at this time.')
                return render(request, 'appointments/appointment_reschedule.html', {'appointment': appointment})
            
            appointment.scheduled_time = new_time
            appointment.save()
            messages.success(request, 'Appointment rescheduled successfully!')
            return redirect('appointment_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error rescheduling appointment: {str(e)}')
    
    context = {'appointment': appointment}
    return render(request, 'appointments/appointment_reschedule.html', context)
