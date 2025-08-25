from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TimeLog
from .serializers import TimeLogSerializer
import json

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'tracker/login.html')

@login_required
def dashboard(request):
    user_logs = TimeLog.objects.filter(user=request.user)
    active_log = user_logs.filter(is_active=True).first()
    
    # Add ISO format for JavaScript
    for log in user_logs:
        log.sign_in_iso = log.sign_in_time.isoformat()
        if log.sign_out_time:
            log.sign_out_iso = log.sign_out_time.isoformat()
    
    if active_log:
        active_log.sign_in_iso = active_log.sign_in_time.isoformat()
    
    return render(request, 'tracker/dashboard.html', {
        'user_logs': user_logs,
        'active_log': active_log
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def sign_in(request):
    # Check if user already has an active session
    active_log = TimeLog.objects.filter(user=request.user, is_active=True).first()
    if active_log:
        return JsonResponse({'error': 'User already signed in'}, status=400)
    
    time_log = TimeLog.objects.create(user=request.user)
    return JsonResponse({
        'success': True,
        'message': 'Signed in successfully',
        'sign_in_time': time_log.sign_in_time.isoformat()
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def sign_out(request):
    active_log = TimeLog.objects.filter(user=request.user, is_active=True).first()
    if not active_log:
        return JsonResponse({'error': 'No active session found'}, status=400)
    
    active_log.sign_out()
    return JsonResponse({
        'success': True,
        'message': 'Signed out successfully',
        'sign_out_time': active_log.sign_out_time.isoformat(),
        'duration': active_log.duration
    })

def logout_view(request):
    # Sign out any active time logs before logging out
    active_log = TimeLog.objects.filter(user=request.user, is_active=True).first()
    if active_log:
        active_log.sign_out()
    logout(request)
    return redirect('login')

# REST API ViewSet
class TimeLogViewSet(viewsets.ModelViewSet):
    serializer_class = TimeLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check for existing active session
        active_log = TimeLog.objects.filter(user=self.request.user, is_active=True).first()
        if active_log:
            return Response({'error': 'User already has an active session'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def sign_in_api(self, request):
        active_log = TimeLog.objects.filter(user=request.user, is_active=True).first()
        if active_log:
            return Response({'error': 'User already signed in'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        time_log = TimeLog.objects.create(user=request.user)
        serializer = self.get_serializer(time_log)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def sign_out_api(self, request):
        active_log = TimeLog.objects.filter(user=request.user, is_active=True).first()
        if not active_log:
            return Response({'error': 'No active session found'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        active_log.sign_out()
        serializer = self.get_serializer(active_log)
        return Response(serializer.data)
