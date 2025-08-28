from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    LoginSerializer,
    DoctorListSerializer
)
from .permissions import IsAdmin, IsDoctorOrAdmin


# API Views
class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class DoctorListView(generics.ListAPIView):
    queryset = CustomUser.objects.filter(role='DOCTOR', is_active=True)
    serializer_class = DoctorListSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserProfileSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_api(request):
    try:
        request.user.auth_token.delete()
    except:
        pass
    return Response({'message': 'Successfully logged out'})


# Web Views
def home(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.POST)
        if serializer.is_valid():
            user = serializer.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return render(request, 'registration/register.html')


def login_view(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Redirect based on user role
            if user.is_admin:
                return redirect('admin_dashboard')
            elif user.is_doctor:
                return redirect('doctor_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def patient_dashboard(request):
    if not request.user.is_patient:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get user's appointments and EMR requests
    appointments = request.user.patient_appointments.all()[:5]
    emr_requests = request.user.emr_requests.all()[:5]
    
    context = {
        'appointments': appointments,
        'emr_requests': emr_requests,
    }
    return render(request, 'dashboard/patient_dashboard.html', context)


@login_required
def doctor_dashboard(request):
    if not request.user.is_doctor:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get doctor's appointments and EMR requests to review
    appointments = request.user.doctor_appointments.filter(status='SCHEDULED')[:5]
    pending_emr_requests = request.user.reviewed_emr_requests.filter(status='PENDING')[:5]
    
    context = {
        'appointments': appointments,
        'pending_emr_requests': pending_emr_requests,
    }
    return render(request, 'dashboard/doctor_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get statistics for admin dashboard
    from appointments.models import Appointment
    from emr.models import EMRRequest
    
    total_users = CustomUser.objects.count()
    total_patients = CustomUser.objects.filter(role='PATIENT').count()
    total_doctors = CustomUser.objects.filter(role='DOCTOR').count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='SCHEDULED').count()
    pending_emr_requests = EMRRequest.objects.filter(status='PENDING').count()
    
    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'pending_emr_requests': pending_emr_requests,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
