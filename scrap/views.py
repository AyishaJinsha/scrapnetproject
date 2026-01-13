from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Profile, Vehicle, ScrapRequest
from .forms import VehicleForm, CustomUserCreationForm

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = request.POST.get('role', 'user')
            Profile.objects.create(user=user, role=role)
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role == 'user':
        return redirect('user_dashboard')
    elif profile.role == 'agency':
        return redirect('agency_dashboard')
    elif profile.role == 'rto':
        return redirect('rto_dashboard')

@login_required
def user_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'user':
        return redirect('dashboard')
    requests = ScrapRequest.objects.filter(user=request.user)
    total_requests = requests.count()
    active_requests = requests.filter(status__in=['submitted', 'reviewed', 'forwarded']).count()
    completed_requests = requests.filter(status__in=['approved', 'rejected']).count()
    pending_requests = requests.filter(status='submitted').count()
    vehicles = Vehicle.objects.filter(scraprequest__user=request.user).distinct()
    total_vehicles = vehicles.count()
    return render(request, 'user_dashboard.html', {
        'requests': requests,
        'total_requests': total_requests,
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'pending_requests': pending_requests,
        'total_vehicles': total_vehicles,
    })

@login_required
def submit_vehicle(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'user':
        return redirect('dashboard')
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save()
            ScrapRequest.objects.create(user=request.user, vehicle=vehicle)
            messages.success(request, 'Vehicle submitted successfully')
            return redirect('user_dashboard')
    else:
        form = VehicleForm()
    return render(request, 'submit_vehicle.html', {'form': form})

@login_required
def view_requests(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'user':
        return redirect('dashboard')
    requests = ScrapRequest.objects.filter(user=request.user)
    return render(request, 'view_requests.html', {'requests': requests})

@login_required
def agency_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        return redirect('dashboard')
    all_requests = ScrapRequest.objects.all()
    pending_requests = all_requests.filter(status='submitted').count()
    in_progress_requests = all_requests.filter(status__in=['reviewed', 'forwarded']).count()
    completed_requests = all_requests.filter(status__in=['approved', 'rejected']).count()
    requests = all_requests.filter(status__in=['submitted', 'reviewed'])
    return render(request, 'agency_dashboard.html', {
        'requests': requests,
        'pending_requests': pending_requests,
        'in_progress_requests': in_progress_requests,
        'completed_requests': completed_requests,
    })

@login_required
def review_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id)
    if request.method == 'POST':
        damage_level = request.POST.get('damage_level')
        scrap_price = request.POST.get('scrap_price')
        scrap_request.damage_level = damage_level
        scrap_request.scrap_price = scrap_price
        scrap_request.status = 'reviewed'
        scrap_request.reviewed_at = timezone.now()
        scrap_request.save()
        return redirect('agency_dashboard')
    return render(request, 'review_request.html', {'scrap_request': scrap_request})

@login_required
def forward_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id, status='reviewed')
    scrap_request.status = 'forwarded'
    scrap_request.forwarded_at = timezone.now()
    scrap_request.save()
    return redirect('agency_dashboard')

@login_required
def rto_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'rto':
        return redirect('dashboard')
    requests = ScrapRequest.objects.filter(status='forwarded')
    awaiting_requests = requests.count()
    return render(request, 'rto_dashboard.html', {
        'requests': requests,
        'awaiting_requests': awaiting_requests,
    })

@login_required
def approve_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'rto':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            scrap_request.status = 'approved'
            scrap_request.approved_at = timezone.now()
        elif action == 'reject':
            scrap_request.status = 'rejected'
        scrap_request.save()
        return redirect('rto_dashboard')
    return render(request, 'approve_request.html', {'scrap_request': scrap_request})
