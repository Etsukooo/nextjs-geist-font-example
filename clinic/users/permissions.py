from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """
    Custom permission to only allow patients to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_patient


class IsDoctor(permissions.BasePermission):
    """
    Custom permission to only allow doctors to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_doctor


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsDoctorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow doctors or admins to access certain views.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                (request.user.is_doctor or request.user.is_admin))


class IsOwnerOrDoctorOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users to access their own data, or doctors/admins to access any data.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the object
        if hasattr(obj, 'patient'):
            is_owner = obj.patient == request.user
        elif hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        else:
            is_owner = obj == request.user
        
        # Allow access if user is owner, doctor, or admin
        return (is_owner or 
                request.user.is_doctor or 
                request.user.is_admin)


class IsPatientOwnerOrDoctorOrAdmin(permissions.BasePermission):
    """
    Custom permission for appointments and EMR - patients can only access their own data,
    doctors and admins can access all data.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Patients can only access their own appointments/EMR requests
        if request.user.is_patient:
            return obj.patient == request.user
        
        # Doctors and admins can access all
        return request.user.is_doctor or request.user.is_admin
