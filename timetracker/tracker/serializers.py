from rest_framework import serializers
from .models import TimeLog

class TimeLogSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TimeLog
        fields = ['id', 'user', 'user_name', 'sign_in_time', 'sign_out_time', 
                 'is_active', 'duration', 'created_at']
        read_only_fields = ['user', 'created_at']
