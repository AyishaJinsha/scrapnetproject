# 🏗️ SCRAPNET SYSTEM ARCHITECTURE

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCRAPNET APPLICATION                          │
│                      (Django Web Framework)                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────▼──────┐  ┌────▼────────┐ ┌──▼─────────────┐
          │  Frontend      │  │  Backend    │ │  Database      │
          │  (HTML/CSS/JS) │  │  (Django)   │ │  (SQLite)      │
          └────────────────┘  └─────────────┘ └────────────────┘
```

---

## 📱 User Interface Layer

```
Browser (Chrome, Firefox, Safari, Edge)
         │
         ├─→ Home Page (/index)
         │
         ├─→ Authentication
         │    ├─ Login (/login)
         │    ├─ Register (/register)
         │    └─ Logout (/logout)
         │
         └─→ Role-Based Dashboards
              │
              ├─ VEHICLE OWNER
              │   ├─ user_dashboard.html
              │   ├─ submit_vehicle.html
              │   ├─ view_requests.html
              │   └─ request_detail.html
              │
              ├─ SCRAP DEALER
              │   ├─ agency_dashboard.html
              │   ├─ review_request.html
              │   └─ request_detail.html
              │
              └─ RTO OFFICER
                  ├─ rto_dashboard.html
                  └─ approve_request.html
```

---

## 🔄 Request Processing Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    SCRAP REQUEST LIFECYCLE                       │
└──────────────────────────────────────────────────────────────────┘

    STAGE 1: USER SUBMISSION
    ┌─────────────────────────────────────────────────────┐
    │ • User registers with role='user'                   │
    │ • User fills vehicle submission form                │
    │ • Uploads vehicle image                             │
    │ • System creates:                                   │
    │   - Vehicle record                                  │
    │   - ScrapRequest (status='submitted')               │
    │   - ActionLog entry                                 │
    │ • Status: SUBMITTED                                 │
    └─────────────────────────────────────────────────────┘
                        │
                        ▼ (1-7 days)
    
    STAGE 2: AGENCY REVIEW
    ┌─────────────────────────────────────────────────────┐
    │ • Agency logs in and views pending requests         │
    │ • Reviews vehicle details and image                 │
    │ • MANUALLY enters:                                  │
    │   - Damage Level (text field)                       │
    │   - Scrap Price (decimal field)                     │
    │ • System:                                           │
    │   - Saves assessment to database                    │
    │   - Sets status='under_agency_review'               │
    │   - Populates agency_id field                       │
    │   - Creates ActionLog                               │
    │   - Sends notification to user                      │
    │ • Agency clicks "Forward to RTO"                    │
    │ • System:                                           │
    │   - Changes status='forwarded'                      │
    │   - Sets forwarded_at timestamp                     │
    │   - Sends notification to user                      │
    │ • Status: FORWARDED                                 │
    └─────────────────────────────────────────────────────┘
                        │
                        ▼ (1-3 days)
    
    STAGE 3: RTO VERIFICATION
    ┌─────────────────────────────────────────────────────┐
    │ • RTO logs in and views forwarded requests          │
    │ • Reviews:                                          │
    │   - Vehicle details                                 │
    │   - Owner information                               │
    │   - Agency assessment                               │
    │   - Complete audit trail                            │
    │ • Makes decision:                                   │
    │                                                     │
    │   OPTION A: APPROVE                                 │
    │   • Clicks "Approve"                                │
    │   • System:                                         │
    │     - Changes status='approved'                     │
    │     - Sets rto_officer_id                           │
    │     - Sets approved_at timestamp                    │
    │     - Enables certificate download                  │
    │     - Creates ActionLog                             │
    │     - Legally de-registers vehicle                  │
    │     - Sends ✅ notification to user                 │
    │                                                     │
    │   OPTION B: REJECT                                  │
    │   • Enters rejection reason                         │
    │   • Clicks "Reject"                                 │
    │   • System:                                         │
    │     - Changes status='rejected'                     │
    │     - Sets rto_officer_id                           │
    │     - Stores rejection reason                       │
    │     - Creates ActionLog                             │
    │     - Sends ❌ notification with reason             │
    │                                                     │
    │ • Status: APPROVED or REJECTED                      │
    └─────────────────────────────────────────────────────┘
                        │
                        ▼ (if approved)
    
    STAGE 4: CERTIFICATE & COMPLETION
    ┌─────────────────────────────────────────────────────┐
    │ • User logs in to dashboard                         │
    │ • Sees "Download Certificate" button                │
    │ • Clicks to download digital certificate            │
    │ • Certificate contains:                             │
    │   - Unique ID                                       │
    │   - Vehicle details                                 │
    │   - Owner details                                   │
    │   - Assessment details                              │
    │   - Approval timestamp                              │
    │   - RTO officer name                                │
    │   - Legal de-registration confirmation              │
    │ • Status: COMPLETED                                 │
    └─────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Relationships

```
                    ┌──────────────────┐
                    │   auth_user      │
                    │   (Django Auth)  │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
        │   scrap_    │ │   scrap_    │ │   scrap_     │
        │   profile   │ │   scrapreq. │ │   vehicle    │
        │  (role)     │ │  (user_id)  │ │              │
        └─────────────┘ │  (rto_id)   │ └──────────────┘
                        │ (agency_id) │
                        └──────┬──────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            ┌──────────────────┐  ┌───────────────┐
            │ scrap_notification│  │ scrap_actionlog
            │  (user_id)       │  │ (user_id)
            │  (message)       │  │ (action)
            │  (is_read)       │  │ (timestamp)
            └──────────────────┘  └───────────────┘
```

---

## 🔐 Role-Based Access Control

```
┌────────────────────────────────────────────────────────────┐
│              ROLE-BASED ACCESS MATRIX                      │
├────────────────────────────────────────────────────────────┤
│ Feature              │ User │ Agency │ RTO │ Admin │
├──────────────────────┼──────┼────────┼─────┼───────┤
│ View Own Requests    │  ✅  │   ✅   │ ✅  │  ✅   │
│ Submit Vehicle       │  ✅  │   ❌   │ ❌  │  ✅   │
│ Review & Assess      │  ❌  │   ✅   │ ❌  │  ✅   │
│ Forward to RTO       │  ❌  │   ✅   │ ❌  │  ✅   │
│ Approve/Reject       │  ❌  │   ❌   │ ✅  │  ✅   │
│ Download Certificate │  ✅  │   ❌   │ ❌  │  ✅   │
│ View All Requests    │  ❌  │   ❌   │ ✅  │  ✅   │
│ Access Admin         │  ❌  │   ❌   │ ❌  │  ✅   │
└────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
USER INTERFACE LAYER
    │
    ├─ HTML Forms
    ├─ CSS Styling
    └─ JavaScript Validation
         │
         ▼
DJANGO VIEW LAYER
    │
    ├─ user_dashboard()
    ├─ submit_vehicle()
    ├─ agency_dashboard()
    ├─ review_request()
    ├─ forward_request()
    ├─ rto_dashboard()
    ├─ approve_request()
    └─ download_certificate()
         │
         ▼
FORM LAYER
    │
    ├─ VehicleForm
    ├─ CustomUserCreationForm
    └─ Form Validation
         │
         ▼
MODEL LAYER (ORM)
    │
    ├─ User (auth.User)
    ├─ Profile
    ├─ Vehicle
    ├─ ScrapRequest
    ├─ Notification
    └─ ActionLog
         │
         ▼
DATABASE LAYER
    │
    └─ SQLite
        ├─ auth_user table
        ├─ scrap_profile table
        ├─ scrap_vehicle table
        ├─ scrap_scraprequest table
        ├─ scrap_notification table
        └─ scrap_actionlog table
```

---

## 🔐 Security Layers

```
┌──────────────────────────────────────────────────────┐
│           SECURITY IMPLEMENTATION STACK              │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  CSRF PROTECTION (Middleware)              │      │
│ │  {% csrf_token %} in all forms             │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  AUTHENTICATION (@login_required)          │      │
│ │  Redirect unauthenticated users to login   │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  AUTHORIZATION (Role-based checks)         │      │
│ │  if profile.role != 'user': redirect()     │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  REQUEST OWNERSHIP (Data isolation)        │      │
│ │  if scrap_request.user != request.user:    │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  PASSWORD SECURITY (Django hashing)        │      │
│ │  PBKDF2 + SHA256                           │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  SQL INJECTION PREVENTION (ORM)            │      │
│ │  All queries via Django ORM                │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
│ ┌────────────────────────────────────────────┐      │
│ │  AUDIT LOGGING (Immutable logs)            │      │
│ │  ActionLog for compliance                  │      │
│ └────────────────────────────────────────────┘      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 📊 Status Workflow State Machine

```
              ┌─────────────┐
              │  SUBMITTED  │ ◄──── User submits vehicle
              └──────┬──────┘
                     │ Agency reviews & saves
                     ▼
         ┌──────────────────────────┐
         │  UNDER_AGENCY_REVIEW     │
         └──────┬───────────────────┘
                │ Agency forwards to RTO
                ▼
         ┌──────────────────────┐
         │   FORWARDED          │
         └──────┬───────────────┘
                │
      ┌─────────┴─────────┐
      │                   │
      ▼                   ▼
  APPROVED            REJECTED
  (RTO approves)      (RTO rejects)
```

---

## 🔄 Notification Flow

```
ACTION                          TRIGGER                 NOTIFICATION
────────────────────────────────────────────────────────────────────
User submits vehicle       ──→ ScrapRequest created ──→ (internal log)
                                                         
Agency reviews             ──→ damage_level saved   ──→ User: "Reviewed"
Agency forwards            ──→ status=forwarded     ──→ User: "Forwarded"
RTO approves               ──→ status=approved      ──→ User: "✅ Approved"
RTO rejects                ──→ status=rejected      ──→ User: "❌ Rejected"
```

---

## 🎯 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     WEB APPLICATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌─────────────┐     ┌────────────┐ │
│  │  Templates   │      │   Views     │     │  Forms     │ │
│  │  (11 files)  │─────▶│  (20+ func) │────▶│  (2 forms) │ │
│  └──────────────┘      └─────────────┘     └────────────┘ │
│         │                    │                    │        │
│         │                    │                    │        │
│         └────────────────────┼────────────────────┘        │
│                              │                             │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │  Django Models   │                    │
│                    │   (6 models)     │                    │
│                    └──────────────────┘                    │
│                              │                             │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │  ORM Layer       │                    │
│                    │  (Database ops)  │                    │
│                    └──────────────────┘                    │
│                              │                             │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │  SQLite Database │                    │
│                    │  (6 tables)      │                    │
│                    └──────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Request Lifecycle Timeline

```
Day 1       Day 3       Day 3       Day 4       Day 4
10:00 AM    2:00 PM     3:30 PM     10:00 AM    10:15 AM
│           │           │           │           │
│           │           │           │           │
▼           ▼           ▼           ▼           ▼

SUBMITTED → REVIEWING → FORWARDED → APPROVED → CERTIFICATE

User        Agency      Agency      RTO         User
submits     reviews     forwards    approves    downloads
vehicle     request     to RTO      request     certificate

Status: "submitted"
        "under_agency_review"
        "forwarded"
        "approved"
```

---

## 🎓 System Complexity Analysis

```
COMPLEXITY METRICS
──────────────────────────────────────────────────────────

Lines of Code:
  ├─ Python (Django): 2000+
  ├─ HTML/CSS/JS: 1500+
  └─ Total: 3500+

Database Objects:
  ├─ Tables: 6 primary + Django defaults
  ├─ Models: 6
  ├─ Foreign Keys: 8
  └─ Relationships: 10+

Views/Functions:
  ├─ Authentication: 3
  ├─ User Module: 4
  ├─ Agency Module: 3
  ├─ RTO Module: 3
  ├─ Utility: 7+
  └─ Total: 20+

Templates:
  ├─ HTML files: 11
  ├─ Total lines: 1000+
  └─ Mobile responsive: Yes

Security Features:
  ├─ Authentication: ✅
  ├─ Authorization: ✅
  ├─ CSRF Protection: ✅
  ├─ SQL Injection Prevention: ✅
  ├─ Audit Logging: ✅
  ├─ Password Hashing: ✅
  └─ Total: 6+

Testing Coverage:
  ├─ Authentication: ✅
  ├─ All Workflows: ✅
  ├─ Security: ✅
  ├─ Data Integrity: ✅
  └─ UI/UX: ✅
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│              PRODUCTION ENVIRONMENT                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐        ┌──────────────┐          │
│  │   NGINX      │────────│   GUNICORN   │          │
│  │   (Reverse   │        │   (Django    │          │
│  │   Proxy)     │        │   App Server)│          │
│  └──────────────┘        └──────────────┘          │
│         │                       │                  │
│         │ Static Files          │ Application      │
│         └──────────┬────────────┘                  │
│                    │                              │
│         ┌──────────┴──────────┐                   │
│         │                     │                   │
│         ▼                     ▼                   │
│    ┌────────────┐      ┌──────────────┐          │
│    │  /static/  │      │  PostgreSQL  │          │
│    │  (CSS,JS)  │      │  (Database)  │          │
│    └────────────┘      └──────────────┘          │
│                                                   │
└─────────────────────────────────────────────────────┘
```

---

This architecture provides a solid, scalable foundation for the ScrapNet vehicle scrapping management system.
