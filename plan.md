Below is a detailed plan outlining every dependent file/changelog along with considerations for error handling, best practices, and a modern, responsive UI design using Django templates with Bootstrap styling.

---

## Project Overview

We will create a Django project named “clinic” with several apps:
- **users** – Implements a custom user model (with roles: Patient, Doctor, Admin), registration/login endpoints, and role-based permissions.
- **appointments** – Handles appointment booking, rescheduling, cancellation; includes models, REST API endpoints, and patient/doctor UI pages.
- **emr** – Manages EMR requests, file uploads, and approvals/denials with doctors/admin access.
- **dashboard** (or integrated within appointments/emr) – Provides analytics for admins and doctors (e.g., appointments per week, pending EMR requests).

The REST API will be built with Django REST Framework (DRF) using class-based ViewSets and proper permission classes. All file uploads (EMRs) will be stored locally and emails (if any) routed to the console.

---

## Detailed File/Change Plan

### 1. Clinic Project Setup

#### File: manage.py  
- No major modifications; used as the project entry point.

#### File: clinic/settings.py  
- **Add Installed Apps:**  
  - Add `'rest_framework'`, `'users'`, `'appointments'`, and `'emr'`.  
- **Database:**  
  - Configure `DATABASES` for SQLite (default demo).  
- **Custom User Model:**  
  - Set `AUTH_USER_MODEL = 'users.CustomUser'`.  
- **Static & Media:**  
  - Define `STATIC_URL`, `STATICFILES_DIRS` (if any), and `MEDIA_URL`, `MEDIA_ROOT` (for EMR file uploads).  
- **Email Backend:**  
  - Set `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`.  
- **DRF Settings:**  
  - Configure the `REST_FRAMEWORK` setting with default session authentication and permissions.

#### File: clinic/urls.py  
- **Include URL Routes:**  
  - Include `admin/` for Django Admin.  
  - Route `/api/users/` to users.urls, `/api/appointments/` to appointments.urls, `/api/emr/` to emr.urls.  
  - Optionally, include `/dashboard/` for analytics views.

---

### 2. Users App

#### File: users/models.py  
- **CustomUser Model:**  
  - Inherit from Django’s `AbstractUser` and add a `role` field with choices (e.g., PATIENT, DOCTOR, ADMIN).  
  - Ensure proper indexing and validations.

#### File: users/serializers.py  
- **User Serializers:**  
  - Create serializers for registration and profile (with role validation).  
  - Validate unique fields (e.g., email).

#### File: users/views.py  
- **Authentication Endpoints:**  
  - Use DRF Generic Views or ViewSets to create endpoints for registration, login, and profile management.  
  - Apply proper error handling and return descriptive error messages.

#### File: users/urls.py  
- **Route Endpoints:**  
  - Map endpoints like `/register/`, `/login/`, and `/profile/`.

---

### 3. Appointments App

#### File: appointments/models.py  
- **Appointment Model:**  
  - Fields: `patient` (ForeignKey to CustomUser), `doctor` (ForeignKey), `scheduled_time` (DateTimeField), `status` (choices: scheduled, canceled, completed), `notes`, and `created_at`.  
  - Add validations (e.g., time conflicts).

#### File: appointments/serializers.py  
- **Appointment Serializer:**  
  - Create a serializer that maps all fields and validates scheduling logic.

#### File: appointments/views.py  
- **API Views/ViewSet:**  
  - Implement CRUD operations using DRF’s ModelViewSet.  
  - Use custom permission classes to restrict patients (can only view their own appointments) and allow doctors/admins enhanced permissions.  
  - Control error handling (e.g., invalid date/time, double bookings).

#### File: appointments/urls.py  
- **URL Routing:**  
  - Use DRF’s DefaultRouter to register the appointments ViewSet.

#### UI Templates (under templates/appointments/)  
- **appointment_list.html:**  
  - Modern, clean table view using Bootstrap.  
  - Display available slots, user bookings with forms for booking/rescheduling/cancellation.  
  - Use proper typography, spacing, and conditional messages for errors.

---

### 4. EMR App

#### File: emr/models.py  
- **EMRRequest Model:**  
  - Fields: `patient` (ForeignKey), `requested_on` (auto_now_add), `status` (choices: pending, approved, denied), optional `file` (FileField with upload_to set to a local folder), and `approval_notes`.  
  - Enforce validations on file uploads.

#### File: emr/serializers.py  
- **EMRRequest Serializer:**  
  - Build serializer that handles creation, updates (approval/denial) and validates file uploads.

#### File: emr/views.py  
- **API Views/ViewSet:**  
  - Use DRF’s ModelViewSet to implement CRUD endpoints.  
  - Patients can only create and view their own requests; doctors and admins can update status and upload EMR files.  
  - Include error handling for file type/size issues.

#### File: emr/urls.py  
- **Routing:**  
  - Define REST endpoints using a router similar to appointments.

#### UI Templates (under templates/emr/)  
- **emr_request.html:**  
  - A form for patients to request access to their EMRs.  
  - For doctors/admins, include controls for reviewing applications, uploading EMR files, and providing comments.  
  - Use Bootstrap forms with modern spacing and error info.

---

### 5. Dashboard & Analytics

#### File: dashboard/views.py (or integrated views)  
- **Dashboard Views for Admin/Doctor:**  
  - Query analytics data (e.g., weekly appointment counts, pending EMR requests).  
  - Pass the data to templates for rendering.

#### File: dashboard/urls.py  
- **Define Routes:**  
  - Routes such as `/dashboard/admin/` for admin and `/dashboard/doctor/` for doctors.

#### UI Templates (under templates/dashboard/)  
- **admin_dashboard.html / doctor_dashboard.html:**  
  - Use a grid layout with Bootstrap.  
  - Present charts/tables (using simple HTML tables or JavaScript-based chart libraries if needed) with clear typographic hierarchy and spacing.  
  - No external images; if required, use `<img src="https://placehold.co/800x600?text=Dashboard+analytics+chart+placeholder"` with proper alt text and onerror fallback.

---

### 6. REST API Endpoints and Security

- **Permissions & Authentication:**  
  - In each ViewSet (appointments, emr) enforce DRF’s `IsAuthenticated` and add custom permission classes for role-based access.  
  - Ensure that patients cannot access other patients’ data, and that only doctors/admins can modify EMR requests.  
- **Error Handling:**  
  - Use try/except in views; return proper HTTP status codes and error messages for invalid input.  
  - Validate data in serializers robustly.

---

### 7. UI/UX Considerations

- **Modern, Responsive Design:**  
  - Base layout defined in `templates/base.html` with a responsive navbar that changes links based on the authenticated user’s role.  
  - Use Bootstrap’s container, grid, and form classes for a clean look.  
  - Typography, spacing, and colors are to be consistent across all pages using CSS in a global stylesheet (e.g., base.css).
- **Accessibility & Error Reporting:**  
  - Include clear error messages in form validations.  
  - Use semantic HTML elements and aria-labels where necessary.

---

## Summary

- The clinic system is structured as a Django project with apps for users, appointments, and EMR.  
- A custom user model (with roles) is created in the users app, with its own REST endpoints.  
- Appointments and EMR requests each have models, serializers, viewsets, and dedicated URL routes ensuring role-based access.  
- UI templates use Bootstrap for a modern, responsive design; pages include dynamic dashboards for doctors/admins.  
- The REST API is built with DRF and enforces strict authentication and custom permissions for role-aware access.  
- Error handling is integrated via serializer validations and try/except blocks in views while returning correct HTTP responses.  
- Local file storage and a console email backend are used to simplify development and demo deployments.  
- Analytics views aggregate key metrics and are rendered in a stylish dashboard using clean typography and spacing.
