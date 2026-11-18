from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from .models import UserProfile
from urllib.parse import urlparse, parse_qs, unquote
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from .models import (UserProfile,Client,Employee,Project,ProjectDetail)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST



def home(request):
    return render(request, "home.html")

def logout_page(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")

    return redirect("home")
@login_required
def client_profile(request):
    return render(request, "dashboards/client_profile.html")

def login_page(request):
    error = ""
    # if request.user.is_authenticated:
    #     profile = request.user.userprofile

    # if profile.is_owneruser:
    #     return redirect("owner_dashboard")
    # elif profile.is_manageruser:
    #     return redirect("manager_dashboard")
    # elif profile.is_sitemanageruser:
    #     return redirect("sitepm_dashboard")
    # elif profile.is_clientuser:
    #     return redirect("client_dashboard")


    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        
        if user is not None:

            print("LOGIN SUCCESS")

            profile = getattr(user, "userprofile", None)

            if profile is None:
                print("PROFILE NOT FOUND")
                error = "User profile not found."

            elif profile.is_owneruser:
                print("OWNER TRUE")
                login(request, user)
                return redirect("owner_dashboard")

            elif profile.is_manageruser:
                print("MANAGER TRUE")
                login(request, user)
                return redirect("manager_dashboard")

            elif profile.is_sitemanageruser:
                print("SITE MANAGER TRUE")
                login(request, user)
                return redirect("sitepm_dashboard")

            elif profile.is_clientuser:
                print("CLIENT TRUE")
                login(request, user)
                return redirect("client_dashboard")

            else:
                print("NO ROLE")
                error = "User role not assigned."

        else:
            error = "Invalid username or password. Please try again."

    return render(request, "login.html", {"error": error})



@login_required
def owner_dashboard(request):

    # Owner login check
    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.userprofile.is_owneruser:
        return redirect("login")


   
    # DATABASE DATA
  

    clients = Client.objects.all().order_by("-created_at")

    employees = Employee.objects.all().order_by("employee_name")

    projects = (
        Project.objects
        .select_related("client")
        .prefetch_related("details")
        .order_by("-created_at")
    )

    project_details = ProjectDetail.objects.all().order_by("-created_at")


    detail_key_map = {
        "room": "rooms",
        "scope": "scope",
        "assignment": "assignments",
        "status_history": "status_history",
        "site_visit": "site_visits",
        "quotation": "quotations",
        "payment": "payments",
        "design": "designs",
        "material": "materials",
        "execution_task": "execution_tasks",
        "document": "documents",
        "handover": "handover",
        "enquiry": "enquiries",
    }

    # ==================================
    # FINAL JSON
    # ==================================

    all_database_json = {}

    for client in clients:

        # Unique Client Key
        client_key = f"CLI-{client.client_key.hex[:8]}"

        client_data = {
            "client_id": client.client_id,
            "name": client.client_name,
            "phone": client.phone,
            "alternative_phone": client.alternative_phone,
            "email": client.email,
            "projects": {}
        }

        # Only this client's projects
        for project in projects:

            if project.client_id != client.client_id:
                continue

            project_data = {

                "project_information": {
                    "project_type": project.project_type,
                    "location": project.location,
                    "google_map_link": project.google_map_link,
                    "area_sqft": project.area_sqft,
                    "bedroom_count": project.bedroom_count,
                    "living_room_count": project.living_room_count,
                    "kitchen_count": project.kitchen_count,
                    "bathroom_count": project.bathroom_count,
                    "current_status": project.current_status,
                    "enquiry_date": project.enquiry_date,
                    "project_start_date": project.project_start_date,
                    "target_handover_date": project.target_handover_date,
                    "actual_handover_date": project.actual_handover_date,
                },

                "rooms": [],
                "scope": [],
                "assignments": [],
                "status_history": [],
                "site_visits": [],
                "quotations": [],
                "payments": [],
                "designs": [],
                "materials": [],
                "execution_tasks": [],
                "documents": [],
                "handover": [],
                "enquiries": [],
            }

            # Get details belonging to this project
            for detail in project.details.all():

                key = detail_key_map.get(detail.detail_type)

                if key:
                    project_data[key].append({

                        "detail_id": detail.detail_id,
                        "data": detail.detail_data,
                        "created_by_id": detail.created_by_id,
                        "created_at": detail.created_at,
                        "updated_at": detail.updated_at,

                    })

            # Project ID as JSON key
            client_data["projects"][project.project_code] = project_data

        # Random Client Key as parent JSON key
        all_database_json[client_key] = client_data

  
        # PROJECT STATUS COUNTS
      

        total_projects = projects.count()

        enquiry_count = projects.filter(
            current_status="enquiry"
        ).count()

        quotation_count = projects.filter(
            current_status="quotation"
        ).count()

        site_visit_count = projects.filter(
            current_status="site_visit"
        ).count()

        payment_count = projects.filter(
            current_status="payment"
        ).count()

        design_count = projects.filter(
            current_status="3d_design"
        ).count()

        material_count = projects.filter(
            current_status="material_selection"
        ).count()

        execution_count = projects.filter(
            current_status="execution"
        ).count()

        hold_count= projects.filter(
            current_status="hold"
        ).count()
        discontinued_count = projects.filter(
            current_status="discontinue"
        ).count()
        completed_projects = projects.filter(
            current_status="handover"
        ).count()
        
       
        

        ongoing_projects = total_projects - completed_projects
        
       

        context = {

            "clients": clients,
            "employees": employees,
            "projects": projects,
            "project_details": project_details,

            # General Counts
            "total_clients": clients.count(),
            "total_employees": employees.count(),
            "total_projects": total_projects,
            "total_details": project_details.count(),

            # Project Summary
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
            "enquiry_count": enquiry_count,
            "quotation_count": quotation_count,
            "site_visit_count": site_visit_count,
            "payment_count": payment_count,
            "design_count": design_count,
            "material_count": material_count,
            "execution_count": execution_count,
            "discontinued_projects": discontinued_count,
            "hold_projects": hold_count,
            # JSON Data
            "all_database_json": all_database_json,

        }
    
    return render(request,"owner/dashboard.html",context)

@login_required(login_url='login')
@never_cache

def owner_project_map(request):

    if not request.user.userprofile.is_owneruser:
        return redirect('login')

    return render(request, 'owner/projects_map.html', {
        'page_title': 'Project Map',
    })


@login_required(login_url='login')
@never_cache
def owner_projects(request):

    profile = request.user.userprofile

    if not profile.is_owneruser:
        return redirect('login')

    # ==================================
    # DATABASE DATA
    # ==================================

    clients = Client.objects.all().order_by("-created_at")

    employees = Employee.objects.all().order_by("employee_name")

    projects = (
        Project.objects
        .select_related("client")
        .prefetch_related("details")
        .order_by("-created_at")
    )

    project_details = ProjectDetail.objects.all().order_by("-created_at")

    # ==================================
    # DETAIL TYPES
    # ==================================

    detail_key_map = {
        "room": "rooms",
        "scope": "scope",
        "assignment": "assignments",
        "status_history": "status_history",
        "site_visit": "site_visits",
        "quotation": "quotations",
        "payment": "payments",
        "design": "designs",
        "material": "materials",
        "execution_task": "execution_tasks",
        "document": "documents",
        "handover": "handover",
        "enquiry": "enquiries",
    }

    # ==================================
    # FINAL JSON
    # ==================================

    all_database_json = {}

    for client in clients:

        # Unique Client Key
        client_key = f"CLI-{client.client_key.hex[:8]}"

        client_data = {
            "client_id": client.client_id,
            "name": client.client_name,
            "phone": client.phone,
            "alternative_phone": client.alternative_phone,
            "email": client.email,
            "projects": {}
        }

        # Only this client's projects
        for project in projects:

            if project.client_id != client.client_id:
                continue

            project_data = {

                "project_information": {
                    "project_type": project.project_type,
                    "location": project.location,
                    "google_map_link": project.google_map_link,
                    "area_sqft": project.area_sqft,
                    "bedroom_count": project.bedroom_count,
                    "living_room_count": project.living_room_count,
                    "kitchen_count": project.kitchen_count,
                    "bathroom_count": project.bathroom_count,
                    "current_status": project.current_status,
                    "enquiry_date": project.enquiry_date,
                    "project_start_date": project.project_start_date,
                    "target_handover_date": project.target_handover_date,
                    "actual_handover_date": project.actual_handover_date,
                },

                "rooms": [],
                "scope": [],
                "assignments": [],
                "status_history": [],
                "site_visits": [],
                "quotations": [],
                "payments": [],
                "designs": [],
                "materials": [],
                "execution_tasks": [],
                "documents": [],
                "handover": [],
                "enquiries": [],
            }

            # Get details belonging to this project
            for detail in project.details.all():

                key = detail_key_map.get(detail.detail_type)

                if key:
                    project_data[key].append({

                        "detail_id": detail.detail_id,
                        "data": detail.detail_data,
                        "created_by_id": detail.created_by_id,
                        "created_at": detail.created_at,
                        "updated_at": detail.updated_at,

                    })

            # Project ID as JSON key
            client_data["projects"][project.project_code] = project_data

        # Random Client Key as parent JSON key
        all_database_json[client_key] = client_data

        # PROJECT STATUS COUNTS
        

        total_projects = projects.count()

        enquiry_count = projects.filter(
            current_status="enquiry"
        ).count()

        quotation_count = projects.filter(
            current_status="quotation"
        ).count()

        site_visit_count = projects.filter(
            current_status="site_visit"
        ).count()

        payment_count = projects.filter(
            current_status="payment"
        ).count()

        design_count = projects.filter(
            current_status="3d_design"
        ).count()

        material_count = projects.filter(
            current_status="material_selection"
        ).count()

        execution_count = projects.filter(
            current_status="execution"
        ).count()

        handover_count = projects.filter(
            current_status="handover"
        ).count()
        

        completed_projects = handover_count

        ongoing_projects = total_projects - completed_projects

        # ==================================
        # DASHBOARD CONTEXT
        # ==================================

        context = {

            "clients": clients,
            "employees": employees,
            "projects": projects,
            "project_details": project_details,

            # General Counts
            "total_clients": clients.count(),
            "total_employees": employees.count(),
            "total_projects": total_projects,
            "total_details": project_details.count(),

            # Project Summary
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,

            # Individual Status Counts
            "enquiry_count": enquiry_count,
            "quotation_count": quotation_count,
            "site_visit_count": site_visit_count,
            "payment_count": payment_count,
            "design_count": design_count,
            "material_count": material_count,
            "execution_count": execution_count,
            "handover_count": handover_count,

            # JSON Data
            "all_database_json": all_database_json,

        }

        # print(context)

        return render(request,"owner/projects.html",context)


@login_required(login_url='login')
@never_cache
@require_POST
def update_project_status(request, project_id):

    profile = request.user.userprofile

    # Owner permission check
    if not profile.is_owneruser:
        return redirect('login')

    # Get selected project
    project = get_object_or_404(
        Project,
        project_id=project_id
    )

    # Get new status from HTML form
    new_status = request.POST.get('current_status', '').strip()

    # Validate status using model choices
    valid_statuses = [
        choice[0]
        for choice in Project._meta.get_field(
            'current_status'
        ).choices
    ]

    if new_status not in valid_statuses:

        messages.error(request, "Invalid project status.")

        return redirect('owner_projects')

    # Update database
    old_status = project.current_status

    project.current_status = new_status
    project.save()

    messages.success(
        request,
        f"{project.project_code} status updated successfully!"
    )

    return redirect('owner_projects')

@login_required(login_url='login')
@never_cache
def owner_team(request):
    profile = request.user.userprofile

    if not profile.is_owneruser:
        return redirect('login')

    team_members = UserProfile.objects.filter(
        is_manageruser=True
    ) | UserProfile.objects.filter(
        is_sitemanageruser=True
    )

    team_members = team_members.select_related('user').order_by('user__username')

    return render(request, 'owner/team.html', {
        'team_members': team_members,
        'total_members': team_members.count(),
        'manager_count': team_members.filter(is_manageruser=True).count(),
        'sitepm_count': team_members.filter(is_sitemanageruser=True).count(),
    })

@login_required
def manager_dashboard(request):
    if not request.user.userprofile.is_manageruser:
        return redirect("login")

    return render(request, "manager/dashboard.html")


@login_required
def sitepm_dashboard(request):
    if not request.user.userprofile.is_sitemanageruser:
        return redirect("login")
    print("Its Working")
    return render(request, "sitepm/dashboard.html")


@login_required
def client_dashboard(request):
    if not request.user.userprofile.is_clientuser:
        return redirect("login")

    return render(request, "client/dashboard.html")


@transaction.atomic
def client_booking(request):

    if request.method == "POST":

        client_name = request.POST.get("client_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        location = request.POST.get("location", "").strip()
        project_type = request.POST.get("project_type", "").strip()

        errors = []

        if not client_name:
            errors.append("Please enter your name.")

        if not phone:
            errors.append("Please enter your phone number.")

        if not location:
            errors.append("Please enter your project location.")

        if not project_type:
            errors.append("Please select your project type.")

        try:
            area = request.POST.get("area_sqft", "").strip()
            area_sqft = Decimal(area) if area else None

            if area_sqft is not None and area_sqft <= 0:
                errors.append("Area must be greater than zero.")

        except InvalidOperation:
            area_sqft = None
            errors.append("Please enter a valid area.")

        try:
            bedroom_count = int(request.POST.get("bedroom_count") or 0)
            living_count = int(request.POST.get("living_room_count") or 0)
            kitchen_count = int(request.POST.get("kitchen_count") or 0)
            bathroom_count = int(request.POST.get("bathroom_count") or 0)

            if min(bedroom_count, living_count, kitchen_count, bathroom_count) < 0:
                errors.append("Room counts cannot be negative.")

        except ValueError:
            bedroom_count = living_count = kitchen_count = bathroom_count = 0
            errors.append("Please enter valid room counts.")

        if errors:
            return render(request, "booking/client_booking.html", {
                "form_errors": errors
            })

        # Existing client phone number irundha reuse pannuvom
        client = Client.objects.filter(phone=phone).first()

        if client:
            client.client_name = client_name
            if email:
                client.email = email
            client.save()
        else:
            client = Client.objects.create(
                client_name=client_name,
                phone=phone,
                email=email or None
            )

        # Unique project code generate pannuvom
        project_code = (
            f"IBK-{timezone.localdate():%y%m%d}-"
            f"{uuid4().hex[:6].upper()}"
        )

        project = Project.objects.create(
            project_code=project_code,
            client=client,
            location=location,
            google_map_link=request.POST.get("google_map_link", "").strip(),
            project_type=project_type,
            area_sqft=area_sqft,
            bedroom_count=bedroom_count,
            living_room_count=living_count,
            kitchen_count=kitchen_count,
            bathroom_count=bathroom_count,
            current_status="enquiry"
        )

        # Extra booking information save pannuvom
        ProjectDetail.objects.create(
            project=project,
            detail_type="enquiry",
            detail_data={
                "property_type": request.POST.get("property_type", ""),
                "budget": request.POST.get("budget", ""),
                "message": request.POST.get("message", ""),
                "source": "public_website"
            }
        )

        messages.success(
            request,
            "Your enquiry has been submitted successfully! "
            "Our team will contact you soon."
        )

        return redirect("client_booking")

    return render(request, "booking/client_booking.html")
