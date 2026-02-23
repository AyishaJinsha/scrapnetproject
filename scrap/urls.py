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
    path('request/<int:request_id>/', views.view_request_detail, name='request_detail'),
    path('agency_dashboard/', views.agency_dashboard, name='agency_dashboard'),
    path('review_request/<int:request_id>/', views.review_request, name='review_request'),
    path('forward_request/<int:request_id>/', views.forward_request, name='forward_request'),
    path('rto_dashboard/', views.rto_dashboard, name='rto_dashboard'),
    path('approve_request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('download_certificate/<int:request_id>/', views.download_certificate, name='download_certificate'),
]