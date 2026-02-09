from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('user', 'Vehicle Owner'),
        ('agency', 'Scrap Dealer'),
        ('rto', 'Transport Authority'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Vehicle(models.Model):
    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50)
    age = models.PositiveIntegerField()  # in years
    mileage = models.PositiveIntegerField()  # in km
    image = models.ImageField(upload_to='vehicle_images/', blank=True, null=True)

    def __str__(self):
        return self.registration_number

class ScrapRequest(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_agency_review', 'Under Agency Review'),
        ('forwarded', 'Forwarded to RTO'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scrap_requests')
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    damage_level = models.CharField(max_length=50, blank=True, null=True)
    scrap_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    forwarded_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Request by {self.user.username} for {self.vehicle.registration_number}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"

class ActionLog(models.Model):
    scrap_request = models.ForeignKey(ScrapRequest, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} on {self.scrap_request} at {self.timestamp}"
