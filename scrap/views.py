from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Profile, Vehicle, ScrapRequest, Notification, ActionLog
from .forms import VehicleForm, CustomUserCreationForm
import logging
from . import ml_model   # ← ML integration (loaded once at startup)

logger = logging.getLogger(__name__)

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
    requests = ScrapRequest.objects.filter(user=request.user).select_related('vehicle', 'agency')
    total_requests = requests.count()
    active_requests = requests.filter(status__in=['submitted', 'under_agency_review', 'forwarded']).count()
    completed_requests = requests.filter(status__in=['approved', 'rejected']).count()
    pending_requests = requests.filter(status='submitted').count()
    approved_requests = requests.filter(status='approved').count()
    vehicles = Vehicle.objects.filter(scraprequest__user=request.user).distinct()
    total_vehicles = vehicles.count()
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    return render(request, 'user_dashboard.html', {
        'requests': requests,
        'total_requests': total_requests,
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'total_vehicles': total_vehicles,
        'notifications': notifications,
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
    all_requests = ScrapRequest.objects.filter(
        status__in=['submitted', 'under_agency_review']
    ).select_related('vehicle', 'user')
    pending_requests = all_requests.filter(status='submitted').count()
    in_review_requests = all_requests.filter(status='under_agency_review').count()
    forwarded_requests = ScrapRequest.objects.filter(status='forwarded', agency=request.user).count()
    completed_requests = ScrapRequest.objects.filter(
        agency=request.user,
        status__in=['approved', 'rejected']
    ).count()
    requests = all_requests
    return render(request, 'agency_dashboard.html', {
        'requests': requests,
        'pending_requests': pending_requests,
        'in_review_requests': in_review_requests,
        'forwarded_requests': forwarded_requests,
        'completed_requests': completed_requests,
    })

@login_required
def review_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id, status__in=['submitted', 'under_agency_review'])
    if request.method == 'POST':
        damage_level = request.POST.get('damage_level')
        scrap_price = request.POST.get('scrap_price')
        scrap_request.damage_level = damage_level
        scrap_request.scrap_price = scrap_price
        scrap_request.status = 'under_agency_review'
        scrap_request.agency = request.user
        scrap_request.reviewed_at = timezone.now()
        scrap_request.save()
        
        ActionLog.objects.create(
            scrap_request=scrap_request,
            user=request.user,
            action='Agency Review',
            details=f"Damage Level: {damage_level}, Scrap Price: ₹{scrap_price}"
        )
        
        Notification.objects.create(
            user=scrap_request.user,
            message=f"Your vehicle {scrap_request.vehicle.registration_number} has been reviewed by the scrap dealer. Damage Level: {damage_level}, Estimated Price: ₹{scrap_price}"
        )
        
        messages.success(request, 'Review details saved. You can now forward it to RTO.')
        return redirect('agency_dashboard')
    return render(request, 'review_request.html', {'scrap_request': scrap_request})

@login_required
def forward_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id, status='under_agency_review')
    
    if not scrap_request.damage_level or not scrap_request.scrap_price:
        messages.error(request, 'Please complete the review details before forwarding.')
        return redirect('review_request', request_id=scrap_request.id)

    scrap_request.status = 'forwarded'
    scrap_request.forwarded_at = timezone.now()
    scrap_request.save()

    ActionLog.objects.create(
        scrap_request=scrap_request,
        user=request.user,
        action='Forwarded to RTO',
        details=f"Request forwarded to RTO for final approval. Damage: {scrap_request.damage_level}, Price: ₹{scrap_request.scrap_price}"
    )

    Notification.objects.create(
        user=scrap_request.user,
        message=f"Your scrap request for {scrap_request.vehicle.registration_number} has been forwarded to RTO for final approval."
    )

    messages.success(request, 'Request forwarded to RTO successfully.')
    return redirect('agency_dashboard')

# ══════════════════════════════════════════════════════════════
# ML ANALYSIS VIEW  (Agency Only)
# ══════════════════════════════════════════════════════════════

@login_required
def ml_analyze_vehicle(request, request_id):
    """
    Agency triggers ML analysis on a submitted vehicle.

    Security:
    • Only agency role can access.
    • If already ML-processed, further predictions are blocked.

    On POST:
    • Runs damage CNN → sets damage_level
    • Runs price regressor → sets scrap_price
    • Sets ml_processed = True, prediction_timestamp = now
    • Creates ActionLog entry + notifies the vehicle owner
    """
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'agency':
        messages.error(request, 'Only agency users can run ML analysis.')
        return redirect('dashboard')

    scrap_request = get_object_or_404(ScrapRequest, id=request_id)

    # ── Guard: prevent repeated predictions ───────────────────
    if scrap_request.ml_processed:
        messages.warning(
            request,
            f'ML analysis already completed for this vehicle. '
            f'Damage: {scrap_request.damage_level}, Price: ₹{scrap_request.scrap_price}'
        )
        return redirect('agency_dashboard')

    if request.method == 'POST':
        vehicle = scrap_request.vehicle

        # ── 1. Damage Detection ───────────────────────────────
        damage_level = "Medium"   # default
        if vehicle.image and vehicle.image.name:
            import time
            start_ml = time.time()
            try:
                image_path = vehicle.image.path
                damage_level = ml_model.predict_damage(image_path)
                ml_duration = time.time() - start_ml
                logger.info(f"Total ML Analysis time: {ml_duration:.4f}s")
            except Exception as e:
                messages.warning(request, f'Image prediction failed ({e}). Using rule-based fallback.')
                damage_level = ml_model._rule_based_damage(vehicle.image.path if vehicle.image else "")
        else:
            # No image uploaded – use rule-based defaults based on age
            age = vehicle.age
            if age < 5:
                damage_level = "Low"
            elif age < 12:
                damage_level = "Medium"
            else:
                damage_level = "High"

        # ── 2. Price Prediction ───────────────────────────────
        scrap_price = ml_model.predict_price(
            age=vehicle.age,
            mileage=vehicle.mileage,
            vehicle_type=vehicle.vehicle_type,
            damage_level=damage_level,
        )

        # ── 3. Save to database ───────────────────────────────
        scrap_request.damage_level        = damage_level
        scrap_request.scrap_price         = scrap_price
        scrap_request.ml_processed        = True
        scrap_request.prediction_timestamp = timezone.now()
        scrap_request.status              = 'under_agency_review'
        scrap_request.agency              = request.user
        scrap_request.reviewed_at         = timezone.now()
        scrap_request.save()

        # ── 4. Action log ─────────────────────────────────────
        ActionLog.objects.create(
            scrap_request=scrap_request,
            user=request.user,
            action='ML Analysis Completed',
            details=(
                f'AI Damage Level: {damage_level} | '
                f'AI Scrap Price: ₹{scrap_price} | '
                f'Timestamp: {scrap_request.prediction_timestamp.strftime("%d-%m-%Y %H:%M:%S")}'
            ),
        )

        # ── 5. Notify vehicle owner ───────────────────────────
        Notification.objects.create(
            user=scrap_request.user,
            message=(
                f'🤖 AI Analysis completed for your vehicle '
                f'{vehicle.registration_number}. '
                f'Damage Level: {damage_level} | '
                f'Estimated Scrap Value: ₹{scrap_price:,.2f}'
            ),
        )

        messages.success(
            request,
            f'✅ ML Analysis Done! Damage: {damage_level}, Price: ₹{scrap_price:,.2f}'
        )
        return redirect('agency_dashboard')

    # GET → show confirmation page
    return render(request, 'ml_analyze.html', {'scrap_request': scrap_request})

@login_required
def rto_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'rto':
        return redirect('dashboard')
    
    # Prefetch logs and vehicle data
    requests = ScrapRequest.objects.filter(status='forwarded').select_related(
        'vehicle', 'user', 'agency'
    ).prefetch_related('logs__user').order_by('-forwarded_at')
    
    awaiting_requests = requests.count()
    approved_count = ScrapRequest.objects.filter(status='approved', rto_officer=request.user).count()
    rejected_count = ScrapRequest.objects.filter(status='rejected', rto_officer=request.user).count()
    
    return render(request, 'rto_dashboard.html', {
        'requests': requests,
        'awaiting_requests': awaiting_requests,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })

@login_required
def approve_request(request, request_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'rto':
        return redirect('dashboard')
    scrap_request = get_object_or_404(ScrapRequest, id=request_id, status='forwarded')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            scrap_request.status = 'approved'
            scrap_request.approved_at = timezone.now()
            scrap_request.rto_officer = request.user
            ActionLog.objects.create(
                scrap_request=scrap_request,
                user=request.user,
                action='Approved by RTO',
                details="Vehicle registration cancelled and scrap approved. Digital certificate generated."
            )
            Notification.objects.create(
                user=scrap_request.user,
                message=f"✅ Congratulations! Your scrap request for {scrap_request.vehicle.registration_number} has been APPROVED by RTO. Vehicle registration has been permanently cancelled."
            )
        elif action == 'reject':
            scrap_request.status = 'rejected'
            scrap_request.rto_officer = request.user
            ActionLog.objects.create(
                scrap_request=scrap_request,
                user=request.user,
                action='Rejected by RTO',
                details=f"Request rejected by RTO. Reason: {request.POST.get('rejection_reason', 'Not specified')}"
            )
            Notification.objects.create(
                user=scrap_request.user,
                message=f"❌ Your scrap request for {scrap_request.vehicle.registration_number} has been REJECTED by RTO. Reason: {request.POST.get('rejection_reason', 'Please contact RTO for details')}"
            )
        scrap_request.save()
        return redirect('rto_dashboard')
    return render(request, 'approve_request.html', {'scrap_request': scrap_request})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('user_dashboard')
@login_required
def view_request_detail(request, request_id):
    """View detailed information about a specific scrap request"""
    scrap_request = get_object_or_404(ScrapRequest, id=request_id)
    profile = get_object_or_404(Profile, user=request.user)
    
    # Users can only view their own requests
    if profile.role == 'user' and scrap_request.user != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('user_dashboard')
    
    return render(request, 'request_detail.html', {'scrap_request': scrap_request})

@login_required
def download_certificate(request, request_id):
    """Generate and download a digital scrap certificate as PDF (with reportlab fallback to text)."""
    from django.http import HttpResponse
    from datetime import datetime

    scrap_request = get_object_or_404(ScrapRequest, id=request_id, status='approved')
    profile = get_object_or_404(Profile, user=request.user)

    if scrap_request.user != request.user:
        messages.error(request, 'You do not have permission to download this certificate.')
        return redirect('user_dashboard')

    cert_id = f"SCF-{scrap_request.id:05d}-{scrap_request.approved_at.strftime('%Y%m%d')}"
    vehicle  = scrap_request.vehicle
    owner    = scrap_request.user
    agency   = scrap_request.agency
    rto      = scrap_request.rto_officer
    now_str  = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    # ── Try PDF generation ────────────────────────────────────
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        purple = colors.HexColor('#764ba2')
        dark   = colors.HexColor('#1a1a2e')

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     textColor=purple, fontSize=22, spaceAfter=4, alignment=TA_CENTER)
        sub_style   = ParagraphStyle('Sub', parent=styles['Normal'],
                                     textColor=colors.grey, fontSize=10, alignment=TA_CENTER)
        section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                       textColor=dark, fontSize=12, spaceBefore=14, spaceAfter=6)
        body_style  = styles['Normal']

        def row(label, value):
            return [Paragraph(f'<b>{label}</b>', body_style), Paragraph(str(value), body_style)]

        tbl_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9ff')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f0f0ff')]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e0e0e0')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ])

        elements = [
            Paragraph('🏛️  SCRAPNET', title_style),
            Paragraph('Digital Scrap Certificate – Government Transport Authority', sub_style),
            Paragraph(f'Certificate ID: <b>{cert_id}</b>', sub_style),
            Spacer(1, 0.3*cm),
            HRFlowable(width='100%', thickness=2, color=purple),
            Spacer(1, 0.4*cm),

            Paragraph('Vehicle Details', section_style),
            Table([
                row('Registration Number', vehicle.registration_number),
                row('Vehicle Type',        vehicle.vehicle_type),
                row('Age',                 f'{vehicle.age} years'),
                row('Mileage',             f'{vehicle.mileage:,} km'),
            ], colWidths=[6*cm, 11*cm], style=tbl_style),

            Spacer(1, 0.3*cm),
            Paragraph('Owner Details', section_style),
            Table([
                row('Name',     owner.get_full_name() or owner.username),
                row('Username', owner.username),
                row('Email',    owner.email),
            ], colWidths=[6*cm, 11*cm], style=tbl_style),

            Spacer(1, 0.3*cm),
            Paragraph('Scrap Assessment', section_style),
            Table([
                row('Damage Level',     scrap_request.damage_level or '—'),
                row('Estimated Value',  f'₹{scrap_request.scrap_price:,}'),
                row('ML Processed',     '✅ Yes (AI Analysis)' if scrap_request.ml_processed else 'Manual Assessment'),
                row('ML Timestamp',     scrap_request.prediction_timestamp.strftime('%d-%m-%Y %H:%M:%S')
                                        if scrap_request.prediction_timestamp else '—'),
                row('Scrap Dealer',     agency.get_full_name() or agency.username if agency else '—'),
            ], colWidths=[6*cm, 11*cm], style=tbl_style),

            Spacer(1, 0.3*cm),
            Paragraph('Approval Information', section_style),
            Table([
                row('Submitted Date', scrap_request.submitted_at.strftime('%d-%m-%Y %H:%M:%S')),
                row('Approved Date',  scrap_request.approved_at.strftime('%d-%m-%Y %H:%M:%S')),
                row('Approved By',    rto.get_full_name() or rto.username if rto else 'RTO'),
            ], colWidths=[6*cm, 11*cm], style=tbl_style),

            Spacer(1, 0.5*cm),
            HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e0e0e0')),
            Spacer(1, 0.3*cm),

            Paragraph(
                '<b>STATUS: VEHICLE DE-REGISTERED &amp; APPROVED FOR SCRAPPING</b>',
                ParagraphStyle('Status', parent=body_style,
                               textColor=colors.HexColor('#1b5e20'),
                               backColor=colors.HexColor('#e8f5e9'),
                               alignment=TA_CENTER, fontSize=11,
                               borderPadding=(6, 12, 6, 12))
            ),
            Spacer(1, 0.3*cm),
            Paragraph(
                f'<font color="grey" size="8">This certificate confirms that the above vehicle has been permanently '
                f'de-registered from the transport authority and is approved for scrapping. '
                f'Generated: {now_str} | System: ScrapNet</font>',
                ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER)
            ),
        ]

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'ScrapCertificate_{vehicle.registration_number}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except ImportError:
        # ── Fallback to text ─────────────────────────────────
        pass

    # ── Plain-text fallback ───────────────────────────────────
    ml_line = (f'ML Damage     : {scrap_request.damage_level} (AI predicted)\n'
               f'ML Timestamp  : {scrap_request.prediction_timestamp.strftime("%d-%m-%Y %H:%M:%S")}\n'
               if scrap_request.ml_processed else '')

    certificate_content = f"""
================================================================================
                 SCRAPNET – DIGITAL SCRAP CERTIFICATE
================================================================================

Certificate ID : {cert_id}
Generated      : {now_str}

VEHICLE DETAILS
────────────────────────────────────────────────────────────────────────────────
Registration   : {vehicle.registration_number}
Vehicle Type   : {vehicle.vehicle_type}
Age            : {vehicle.age} years
Mileage        : {vehicle.mileage:,} km

OWNER DETAILS
────────────────────────────────────────────────────────────────────────────────
Name           : {owner.get_full_name() or owner.username}
Email          : {owner.email}

SCRAP ASSESSMENT
────────────────────────────────────────────────────────────────────────────────
Damage Level   : {scrap_request.damage_level or '—'}
Scrap Value    : ₹{scrap_request.scrap_price:,}
{ml_line}Scrap Dealer   : {agency.get_full_name() or agency.username if agency else '—'}

APPROVAL INFORMATION
────────────────────────────────────────────────────────────────────────────────
Submitted      : {scrap_request.submitted_at.strftime('%d-%m-%Y %H:%M:%S')}
Approved       : {scrap_request.approved_at.strftime('%d-%m-%Y %H:%M:%S')}
Approved by    : {rto.get_full_name() or rto.username if rto else 'RTO'}

STATUS: VEHICLE DE-REGISTERED & APPROVED FOR SCRAPPING
================================================================================
This is an electronically generated certificate valid without signature.
================================================================================
"""
    response = HttpResponse(certificate_content, content_type='text/plain')
    filename = f'ScrapCertificate_{vehicle.registration_number}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
