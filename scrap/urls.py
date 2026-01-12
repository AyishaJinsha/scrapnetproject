from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('submit_vehicle/', views.submit_vehicle, name='submit_vehicle'),
    path('view_requests/', views.view_requests, name='view_requests'),
    path('agency_dashboard/', views.agency_dashboard, name='agency_dashboard'),
    path('review_request/<int:request_id>/', views.review_request, name='review_request'),
    path('forward_request/<int:request_id>/', views.forward_request, name='forward_request'),
    path('rto_dashboard/', views.rto_dashboard, name='rto_dashboard'),
    path('approve_request/<int:request_id>/', views.approve_request, name='approve_request'),
]