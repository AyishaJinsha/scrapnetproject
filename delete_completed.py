import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrapnet.settings')
django.setup()

from scrap.models import ScrapRequest

# Find completed requests
completed_requests = ScrapRequest.objects.filter(status__in=['approved', 'rejected'])
count = completed_requests.count()

print(f"Found {count} completed requests.")

if count > 0:
    for req in completed_requests:
        print(f"Deleting Request ID: {req.id}, Status: {req.status}, Vehicle: {req.vehicle.registration_number}")
        # Delete the request
        req.delete()
    print("✅ All completed requests have been deleted.")
else:
    print("No completed requests found to delete.")
