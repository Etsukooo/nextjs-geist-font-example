from rest_framework import serializers
from django.utils import timezone
from .models import EMRRequest, EMRFile
from users.serializers import UserProfileSerializer


class EMRRequestSerializer(serializers.ModelSerializer):
    patient_details = UserProfileSerializer(source='patient', read_only=True)
    reviewed_by_details = UserProfileSerializer(source='reviewed_by', read_only=True)
    
    class Meta:
        model = EMRRequest
        fields = ['id', 'patient', 'requested_on', 'status', 'request_reason',
                 'reviewed_by', 'reviewed_on', 'approval_notes',
                 'patient_details', 'reviewed_by_details']
        read_only_fields = ['id', 'patient', 'requested_on', 'reviewed_by', 'reviewed_on']


class EMRRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMRRequest
        fields = ['request_reason']
    
    def create(self, validated_data):
        # Set the patient to the current user
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class EMRRequestReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMRRequest
        fields = ['status', 'approval_notes']
    
    def validate_status(self, value):
        if value not in ['APPROVED', 'DENIED']:
            raise serializers.ValidationError("Status must be either APPROVED or DENIED.")
        return value
    
    def update(self, instance, validated_data):
        # Set the reviewer and review time
        validated_data['reviewed_by'] = self.context['request'].user
        validated_data['reviewed_on'] = timezone.now()
        return super().update(instance, validated_data)


class EMRFileSerializer(serializers.ModelSerializer):
    patient_details = UserProfileSerializer(source='patient', read_only=True)
    uploaded_by_details = UserProfileSerializer(source='uploaded_by', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EMRFile
        fields = ['id', 'patient', 'file', 'file_name', 'file_type', 'description',
                 'uploaded_by', 'uploaded_on', 'is_accessible', 'file_url',
                 'patient_details', 'uploaded_by_details']
        read_only_fields = ['id', 'file_name', 'file_type', 'uploaded_by', 'uploaded_on']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class EMRFileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMRFile
        fields = ['patient', 'file', 'description', 'is_accessible']
    
    def validate_file(self, value):
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        # Validate file type
        allowed_types = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_types:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        return value
    
    def create(self, validated_data):
        # Set the uploader to the current user
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)
