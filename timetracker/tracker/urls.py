from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'timelogs', views.TimeLogViewSet, basename='timelog')
router.register(r'users', views.UserManagementViewSet, basename='user')

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('sign-out/', views.sign_out, name='sign_out'),
    
    # HR URLs
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/users/add/', views.add_user, name='add_user'),
    path('hr/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('hr/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('hr/users/<int:user_id>/logs/', views.view_user_logs, name='view_user_logs'),
    
    # API
    path('api/', include(router.urls)),
]