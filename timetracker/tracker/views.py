from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TimeLog, UserProfile
from .serializers import TimeLogSerializer, UserSerializer
import json

def is_hr_user(user):
    """Check if user has HR role"""
    if not user.is_authenticated:
        return False
    try:
        return user.userprofile.role == 'hr'  # Change this line
    except UserProfile.DoesNotExist:
        return False

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect based on user role
            try:
                if user.userprofile.is_hr:
                    return redirect('hr_dashboard')
            except UserProfile.DoesNotExist:
                # Create profile for users without one
                UserProfile.objects.create(user=user)
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

# HR Dashboard and User Management Views
@login_required
@user_passes_test(is_hr_user, login_url='/dashboard/')
def hr_dashboard(request):
    # Get all users except superusers
    users = User.objects.all().select_related('userprofile')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(userprofile__department__icontains=search_query) |
            Q(userprofile__position__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    # Statistics
    total_users = User.objects.all().count()
    active_sessions = TimeLog.objects.filter(is_active=True).count()
    hr_users = UserProfile.objects.filter(role='hr').count()
    
    return render(request, 'tracker/hr_dashboard.html', {
        'users': users,
        'search_query': search_query,
        'total_users': total_users,
        'active_sessions': active_sessions,
        'hr_users': hr_users,
    })

@login_required
@user_passes_test(is_hr_user, login_url='/dashboard/')
def add_user(request):
    if request.method == 'POST':
        try:
            # Create user
            user = User.objects.create_user(
                username=request.POST['username'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                password=request.POST['password']
            )
            
            # Create profile
            UserProfile.objects.create(
                user=user,
                role=request.POST['role'],
                employee_id=request.POST.get('employee_id', ''),
                department=request.POST.get('department', ''),
                position=request.POST.get('position', ''),
                phone=request.POST.get('phone', ''),
                hire_date=request.POST.get('hire_date') or None
            )
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('hr_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'tracker/add_user.html')

@login_required
@user_passes_test(is_hr_user, login_url='/dashboard/')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Prevent HR users from editing other HR users
    if is_hr_user(user) and user != request.user:
        messages.error(request, 'You cannot edit other HR users.')
        return redirect('hr_dashboard')
    
    if request.method == 'POST':
        try:
            # Update user
            user.username = request.POST['username']
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.is_active = request.POST.get('is_active') == 'on'
            
            if request.POST.get('password'):
                user.set_password(request.POST['password'])
            
            user.save()
            
            # Update profile
            profile.role = request.POST['role']
            profile.employee_id = request.POST.get('employee_id', '')
            profile.department = request.POST.get('department', '')
            profile.position = request.POST.get('position', '')
            profile.phone = request.POST.get('phone', '')
            profile.hire_date = request.POST.get('hire_date') or None
            profile.save()
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('hr_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    return render(request, 'tracker/edit_user.html', {
        'user_obj': user,
        'profile': profile
    })

@login_required
@user_passes_test(is_hr_user, login_url='/dashboard/')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Prevent HR users from deleting other HR users
    if is_hr_user(user):
        messages.error(request, 'You cannot delete HR users.')
        return redirect('hr_dashboard')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('hr_dashboard')
    
    return render(request, 'tracker/delete_user.html', {'user_obj': user})

@login_required
@user_passes_test(is_hr_user, login_url='/dashboard/')
def view_user_logs(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_logs = TimeLog.objects.filter(user=user)
    
    # Add ISO format for JavaScript
    for log in user_logs:
        log.sign_in_iso = log.sign_in_time.isoformat()
        if log.sign_out_time:
            log.sign_out_iso = log.sign_out_time.isoformat()
    
    return render(request, 'tracker/view_user_logs.html', {
        'user_obj': user,
        'user_logs': user_logs
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
    if request.user.is_authenticated:
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

# HR API ViewSet
class UserManagementViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only HR users can access this
        if not is_hr_user(self.request.user):
            return User.objects.none()
        return User.objects.filter(is_superuser=False).select_related('userprofile')
