## 🚀 SCRAPNET - QUICK START GUIDE

### ⚡ 5-MINUTE SETUP

#### 1. Start the Server (Already Running)
Your development server is running at: **http://localhost:8000**

#### 2. Create Three Test Accounts

**Account 1: Vehicle Owner (User)**
- Go to http://localhost:8000/register/
- Name: John Doe
- Email: john@example.com
- Username: **john_user**
- Password: **Test@1234**
- Role: **Vehicle Owner**
- Click Register

**Account 2: Scrap Dealer (Agency)**
- Register again
- Name: Scrap Dealer Corp
- Email: dealer@example.com
- Username: **dealer_agency**
- Password: **Test@1234**
- Role: **Scrap Dealer**

**Account 3: RTO Officer**
- Register again
- Name: RTO Officer
- Email: rto@example.com
- Username: **rto_officer**
- Password: **Test@1234**
- Role: **Transport Authority**

---

### 📝 COMPLETE WORKFLOW TEST

#### Step 1: Login as User & Submit Vehicle
1. Login with: john_user / Test@1234
2. Click "Submit Vehicle"
3. Fill:
   - Registration: **DL-01-AB-1234**
   - Type: **Sedan**
   - Age: **12**
   - Mileage: **150000**
   - Image: (any car image)
4. Submit

#### Step 2: Login as Agency & Review
1. Logout, Login with: dealer_agency / Test@1234
2. On Agency Dashboard, click "Review"
3. Fill:
   - Damage Level: **Severe**
   - Scrap Price: **150000**
4. Click "Review"
5. Click "Forward" button to send to RTO

#### Step 3: Login as RTO & Approve
1. Logout, Login with: rto_officer / Test@1234
2. On RTO Dashboard, click "Review"
3. Review vehicle and agency assessment
4. Click "Approve Request"

#### Step 4: Login as User & Download Certificate
1. Logout, Login with: john_user / Test@1234
2. See approved request on dashboard
3. Click "Download Certificate" button
4. Certificate file downloads as text file

---

### ✨ KEY FEATURES TO TEST

✅ **Notifications System**
- User notifications appear after each stage
- Click to mark as read

✅ **Request Detail Page**
- Click eye icon (👁️) to see full timeline
- Shows all activity and timestamps

✅ **Status Badges**
- Different colors for different statuses
- Real-time updates

✅ **Role-Based Access**
- Each user can only see their dashboards
- Try accessing wrong page → redirected

✅ **Audit Trail**
- View request details → see activity log
- Shows who did what and when

✅ **Security Features**
- Can't skip steps (e.g., can't forward without assessment)
- Can't access others' requests
- CSRF protection on all forms

---

### 📊 DATABASE STRUCTURE

**6 Main Tables:**
1. `auth_user` - User accounts
2. `scrap_profile` - Role assignment
3. `scrap_vehicle` - Vehicle details
4. `scrap_scraprequest` - Request tracking
5. `scrap_notification` - User notifications
6. `scrap_actionlog` - Audit trail

---

### 🎯 IMPORTANT POINTS

✅ **NO Machine Learning**
- All damage assessment is manual
- All pricing is manual
- No automatic detection

✅ **Manual Assessment**
- Agency must enter damage level
- Agency must enter scrap price
- System just stores and tracks it

✅ **Complete Transparency**
- User can see what agency assessed
- RTO decision is final
- All actions are logged

✅ **Secure & Compliant**
- Role-based access control
- Audit trail for compliance
- Immutable action logs

---

### 🧪 TEST REJECTION FLOW

1. Submit vehicle as user
2. Review as agency
3. On RTO dashboard, click "Review"
4. Click "Reject Request"
5. Enter reason: "Documentation incomplete"
6. Confirm rejection
7. Login as user → see rejection notification

---

### 📱 UI FEATURES

**Dashboard Components:**
- Statistics cards (color-coded)
- Request tables (sortable, interactive)
- Status badges
- Sidebar navigation
- Mobile responsive
- Modern Bootstrap 5 design

**Page Features:**
- Request detail timeline
- Vehicle image display
- Complete audit trail
- Activity log
- Notification panel
- Certificate download

---

### 🔐 SECURITY CHECKS

Try these to verify security:
1. Login as User A, try to access User B's request → Denied
2. Login as Agency, try to access RTO dashboard → Redirected
3. Try to forward request without damage level → Error
4. Try to approve request not forwarded → Error
5. All forms have CSRF token protection

---

### 📞 COMMON ISSUES

**Issue:** Page says "Permission denied"
**Solution:** Make sure you're logged in with correct role

**Issue:** Can't forward request
**Solution:** Make sure you filled in damage level AND scrap price

**Issue:** Image not uploading
**Solution:** File must be image type (jpg, png, gif) and under 10MB

**Issue:** Notification not appearing
**Solution:** Refresh page - notifications load on page load

---

### 🎓 LEARNING OUTCOMES

After completing this test, you'll understand:
- ✅ How role-based systems work
- ✅ Database relationships and foreign keys
- ✅ Workflow management and status transitions
- ✅ Audit trails and compliance
- ✅ User authentication and authorization
- ✅ Django request/response cycle
- ✅ Template rendering with context data
- ✅ Form handling and validation
- ✅ Bootstrap UI/UX patterns

---

### 📚 FILES REFERENCE

**Key Python Files:**
- `/scrap/models.py` - Database models
- `/scrap/views.py` - Business logic
- `/scrap/urls.py` - URL routing
- `/scrap/forms.py` - Form definitions
- `/scrap/admin.py` - Admin panel config

**Key HTML Files:**
- `/scrap/templates/base.html` - Master template
- `/scrap/templates/user_dashboard.html`
- `/scrap/templates/agency_dashboard.html`
- `/scrap/templates/rto_dashboard.html`
- `/scrap/templates/request_detail.html`
- `/scrap/templates/approve_request.html`

**Key Settings:**
- `/scrapnet/settings.py` - Django configuration
- `/scrapnet/urls.py` - Project URL config

---

### ✅ VERIFICATION CHECKLIST

After setup, verify:
- [ ] Server running at localhost:8000
- [ ] Homepage loads (no 404 errors)
- [ ] Can register new user
- [ ] Can login with user account
- [ ] Can submit vehicle
- [ ] Can view user dashboard
- [ ] Different role dashboards exist
- [ ] Can mark notifications as read
- [ ] Request detail page shows timeline
- [ ] Agency can review and forward
- [ ] RTO can approve/reject
- [ ] User can download certificate

---

### 🎉 NEXT STEPS

1. **Test the Complete Workflow** (30 minutes)
   - Follow the 4-step test above

2. **Explore the Code** (1 hour)
   - Read models.py to understand data structure
   - Read views.py to see business logic
   - Check templates to understand UI

3. **Customize** (2+ hours)
   - Add more status options
   - Customize email notifications
   - Add additional vehicle fields
   - Customize certificate format

4. **Deploy** (varies)
   - Set up production server
   - Configure database backup
   - Set up SSL certificate
   - Configure email notifications

---

### 📞 SUPPORT

For detailed information, see:
- `TESTING_GUIDE.md` - Comprehensive testing guide
- `PROJECT_COMPLETION_REPORT.md` - Full technical details
- Django documentation: https://docs.djangoproject.com/

---

**Status:** ✅ READY TO USE  
**Time to Complete Test:** ~30 minutes  
**Server:** http://localhost:8000

🚀 **Start testing now!**
