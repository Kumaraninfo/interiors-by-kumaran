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
from .models import (UserProfile,Client,Employee,Project,ProjectDetail, ProjectRoom,RoomWork,ProjectStageHistory,)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
import json

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

    # ==================================
    # 1. OWNER AUTHENTICATION
    # ==================================

    profile = request.user.userprofile

    if not profile.is_owneruser:
        return redirect('login')


    # ==================================
    # 2. DATABASE DATA
    # ==================================

    clients = Client.objects.all().order_by("-created_at")

    employees = Employee.objects.all().order_by("employee_name")

    projects = Project.objects.select_related(
        "client"
    ).order_by("-created_at")

    project_details = ProjectDetail.objects.all()


    # ==================================
    # 3. PROJECT STATUS PROGRESS
    # ==================================

    progress_map = {
        "enquiry": 1,
        "quotation": 8,
        "site_visit": 25,
        "payment": 50,
        "3d_design": 63,
        "material_selection": 75,
        "execution": 90,
        "handover": 100,
    }


    # ==================================
    # 4. RECENT PROJECTS - LATEST 5
    # ==================================

    recent_projects = []

    latest_projects = projects[:5]

    for project in latest_projects:

        current_status = project.current_status

        progress = progress_map.get(
            current_status,
            0
        )

        recent_projects.append({

            "project_code": project.project_code,

            "client_name": (
                project.client.client_name
                if project.client else "N/A"
            ),

           "location": project.location.title() if project.location else "N/A",

            "current_status": current_status,

            "status": project.get_current_status_display(),

            "progress": progress,

            "target_handover_date": project.target_handover_date,

        })

    # ==================================
    # PROJECT TIMELINE - DATABASE DATA
    # ==================================

    timeline_statuses = [
        {
            "key": "enquiry",
            "label": "Enquiry",
            "icon": "bi bi-chat-square-text",
            "class": "timeline-enquiry",
        },
        {
            "key": "quotation",
            "label": "Quotation",
            "icon": "bi bi-file-earmark-text",
            "class": "timeline-quotation",
        },
        {
            "key": "site_visit",
            "label": "Site Visit",
            "icon": "bi bi-geo-alt",
            "class": "timeline-site",
        },
        {
            "key": "payment",
            "label": "Payment",
            "icon": "bi bi-credit-card",
            "class": "timeline-payment",
        },
        {
            "key": "3d_design",
            "label": "3D Design",
            "icon": "bi bi-box",
            "class": "timeline-design",
        },
        {
            "key": "material_selection",
            "label": "Material Selection",
            "icon": "bi bi-palette",
            "class": "timeline-material",
        },
        {
            "key": "execution",
            "label": "Execution",
            "icon": "bi bi-tools",
            "class": "timeline-execution",
        },
        {
            "key": "handover",
            "label": "Handover",
            "icon": "bi bi-house-check",
            "class": "timeline-handover",
        },
    ]

    project_timeline = []

    for stage in timeline_statuses:

        count = projects.filter(
            current_status=stage["key"]
        ).count()

        # Show only stages that contain projects
        if count > 0:

            project_timeline.append({

                "label": stage["label"],
                "count": count,
                "icon": stage["icon"],
                "class": stage["class"],

            })
    # ==================================
    # 5. PROJECT STATUS COUNTS
    # ==================================

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


    # ==================================
    # 6. DASHBOARD SUMMARY
    # ==================================

    completed_projects = handover_count

    ongoing_projects = total_projects - completed_projects


    # ==================================
    # 7. DASHBOARD CONTEXT
    # ==================================

    context = {

        # Database
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

        # Recent Projects
        "recent_projects": recent_projects,
        "project_timeline": project_timeline,

    }


    # ==================================
    # 8. RENDER DASHBOARD
    # ==================================

    return render(request,"owner/dashboard.html",context)

@login_required(login_url='login')
@never_cache


def owner_project_map(request):

    # ==================================
    # 1. OWNER AUTHENTICATION
    # ==================================

    profile = request.user.userprofile

    if not profile.is_owneruser:
        return redirect('login')


    # ==================================
    # 2. DATABASE DATA
    # ==================================

    clients = Client.objects.all().order_by("-created_at")

    employees = Employee.objects.all().order_by("employee_name")

    projects = Project.objects.select_related(
        "client"
    ).order_by("-created_at")

    project_details = ProjectDetail.objects.all()


    # ==================================
    # 3. PROJECT STATUS PROGRESS
    # ==================================

    progress_map = {
        "enquiry": 1,
        "quotation": 8,
        "site_visit": 25,
        "payment": 50,
        "3d_design": 63,
        "material_selection": 75,
        "execution": 90,
        "handover": 100,
    }


    # ==================================
    # 4. RECENT PROJECTS - LATEST 5
    # ==================================

    recent_projects = []

    latest_projects = projects[:5]

    for project in latest_projects:

        current_status = project.current_status

        progress = progress_map.get(
            current_status,
            0
        )

        recent_projects.append({

            "project_code": project.project_code,

            "client_name": (
                project.client.client_name
                if project.client else "N/A"
            ),

           "location": project.location.title() if project.location else "N/A",

            "current_status": current_status,

            "status": project.get_current_status_display(),

            "progress": progress,

            "target_handover_date": project.target_handover_date,

        })

    # ==================================
    # PROJECT TIMELINE - DATABASE DATA
    # ==================================

    timeline_statuses = [
        {
            "key": "enquiry",
            "label": "Enquiry",
            "icon": "bi bi-chat-square-text",
            "class": "timeline-enquiry",
        },
        {
            "key": "quotation",
            "label": "Quotation",
            "icon": "bi bi-file-earmark-text",
            "class": "timeline-quotation",
        },
        {
            "key": "site_visit",
            "label": "Site Visit",
            "icon": "bi bi-geo-alt",
            "class": "timeline-site",
        },
        {
            "key": "payment",
            "label": "Payment",
            "icon": "bi bi-credit-card",
            "class": "timeline-payment",
        },
        {
            "key": "3d_design",
            "label": "3D Design",
            "icon": "bi bi-box",
            "class": "timeline-design",
        },
        {
            "key": "material_selection",
            "label": "Material Selection",
            "icon": "bi bi-palette",
            "class": "timeline-material",
        },
        {
            "key": "execution",
            "label": "Execution",
            "icon": "bi bi-tools",
            "class": "timeline-execution",
        },
        {
            "key": "handover",
            "label": "Handover",
            "icon": "bi bi-house-check",
            "class": "timeline-handover",
        },
    ]

    project_timeline = []

    for stage in timeline_statuses:

        count = projects.filter(
            current_status=stage["key"]
        ).count()

        # Show only stages that contain projects
        if count > 0:

            project_timeline.append({

                "label": stage["label"],
                "count": count,
                "icon": stage["icon"],
                "class": stage["class"],

            })
    # ==================================
    # 5. PROJECT STATUS COUNTS
    # ==================================

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

    others_count = total_projects - execution_count - design_count
    

    context = {

        # Database
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
        "others_count": others_count,

        # Recent Projects
        "recent_projects": recent_projects,
        "project_timeline": project_timeline,

    }



    return render(request,"owner/projects_map.html",context)




@login_required(login_url='login')
@never_cache
def owner_projects(request):

    profile = getattr(request.user, "userprofile", None)

    if not profile or not profile.is_owneruser:
        return redirect('login')

    # ==================================
    # 1. CREATE NEW PROJECT - POST
    # ==================================

    if request.method == "POST":

        try:
            with transaction.atomic():

                # CLIENT DETAILS
                client_name = request.POST.get("client_name", "").strip()
                phone = request.POST.get("phone", "").strip()
                alternative_phone = request.POST.get("alternative_phone", "").strip()
                email = request.POST.get("email", "").strip()

                # PROJECT DETAILS
                project_type = request.POST.get("project_type", "").strip()
                property_type = request.POST.get("property_type", "").strip()
                location = request.POST.get("location", "").strip()
                google_map_link = request.POST.get("google_map_link", "").strip()

                area = request.POST.get("area_sqft", "").strip()
                budget = request.POST.get("budget", "").strip()
                message = request.POST.get("message", "").strip()

                # VALIDATION
                if not client_name:
                    raise ValueError("Client name is required.")

                if not phone:
                    raise ValueError("Phone number is required.")

                if not email:
                    raise ValueError("Email is required.")

                if not project_type:
                    raise ValueError("Project type is required.")

                if not property_type:
                    raise ValueError("Property type is required.")

                if not location:
                    raise ValueError("Location is required.")

                if not area:
                    raise ValueError("Area is required.")

                if not budget:
                    raise ValueError("Budget is required.")

                area_sqft = Decimal(area)

                if area_sqft <= 0:
                    raise ValueError("Area must be greater than zero.")

                # ROOM COUNTS
                bedroom_count = int(request.POST.get("bedroom_count") or 0)
                living_room_count = int(request.POST.get("living_room_count") or 0)
                kitchen_count = int(request.POST.get("kitchen_count") or 0)
                bathroom_count = int(request.POST.get("bathroom_count") or 0)

                if min(
                    bedroom_count,
                    living_room_count,
                    kitchen_count,
                    bathroom_count
                ) < 0:
                    raise ValueError("Room counts cannot be negative.")

                # ==================================
                # 2. CREATE CLIENT
                # ==================================

                client = Client.objects.create(
                    client_name=client_name,
                    phone=phone,
                    alternative_phone=alternative_phone,
                    email=email
                )

                # ==================================
                # 3. GENERATE PROJECT CODE
                # ==================================

                last_project = Project.objects.filter(
                    project_code__startswith="IBK-"
                ).order_by("-project_id").first()

                if last_project:
                    last_number = int(last_project.project_code.split("-")[1])
                    next_number = max(last_number + 1, 9)
                else:
                    next_number = 9

                project_code = f"IBK-{next_number:04d}"

                # ==================================
                # 4. CREATE PROJECT
                # ==================================

                project = Project.objects.create(
                    project_code=project_code,
                    client=client,
                    location=location,
                    google_map_link=google_map_link,
                    project_type=project_type,
                    area_sqft=area_sqft,
                    bedroom_count=bedroom_count,
                    living_room_count=living_room_count,
                    kitchen_count=kitchen_count,
                    bathroom_count=bathroom_count,
                    current_status="enquiry"
                )

                # ==================================
                # 5. SAVE ENQUIRY DETAILS
                # ==================================

                ProjectDetail.objects.create(
                    project=project,
                    detail_type="enquiry",
                    detail_data={
                        "property_type": property_type,
                        "budget": budget,
                        "message": message,
                        "source": "owner_created"
                    },
                    created_by=request.user
                )

            messages.success(
                request,
                f"{project.project_code} created successfully!"
            )

            return redirect("newproject")

        except (ValueError, InvalidOperation, TypeError) as error:

            messages.error(request, str(error))
            return redirect("newproject")

        except Exception as error:

            print("PROJECT CREATE ERROR:", repr(error))

            messages.error(
                request,
                "Project save failed. Check terminal for the error."
            )

            return redirect("newproject")

    # ==================================
    # 6. GET DATABASE DATA
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
    # 7. DETAIL TYPES
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
    # 8. BUILD CLIENT PROJECT JSON
    # ==================================

    all_database_json = {}

    for client in clients:

        client_key = f"CLI-{client.client_key.hex[:8]}"

        client_data = {
            "client_id": client.client_id,
            "name": client.client_name,
            "phone": client.phone,
            "alternative_phone": client.alternative_phone,
            "email": client.email,
            "projects": {}
        }

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

            client_data["projects"][project.project_code] = project_data

        all_database_json[client_key] = client_data

    # ==================================
    # 9. PROJECT STATUS COUNTS
    # ==================================

    total_projects = projects.count()

    enquiry_count = projects.filter(current_status="enquiry").count()
    quotation_count = projects.filter(current_status="quotation").count()
    site_visit_count = projects.filter(current_status="site_visit").count()
    payment_count = projects.filter(current_status="payment").count()
    design_count = projects.filter(current_status="3d_design").count()
    material_count = projects.filter(current_status="material_selection").count()
    execution_count = projects.filter(current_status="execution").count()
    handover_count = projects.filter(current_status="handover").count()

    completed_projects = handover_count
    ongoing_projects = total_projects - completed_projects

    # ==================================
    # 10. PAGE CONTEXT
    # ==================================

    context = {
        "clients": clients,
        "employees": employees,
        "projects": projects,
        "project_details": project_details,

        "total_clients": clients.count(),
        "total_employees": employees.count(),
        "total_projects": total_projects,
        "total_details": project_details.count(),

        "ongoing_projects": ongoing_projects,
        "completed_projects": completed_projects,

        "enquiry_count": enquiry_count,
        "quotation_count": quotation_count,
        "site_visit_count": site_visit_count,
        "payment_count": payment_count,
        "design_count": design_count,
        "material_count": material_count,
        "execution_count": execution_count,
        "handover_count": handover_count,

        "all_database_json": all_database_json,
    }

    return render(request, "owner/projects.html", context)


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


@login_required
def edit_project(request, project_id):

    project = get_object_or_404(
        Project.objects.select_related("client"),
        project_id=project_id
    )

    profile = getattr(request.user, "userprofile", None)

    if not profile or not profile.is_owneruser:
        messages.error(
            request,
            "You don't have permission to edit this project."
        )
        return redirect("login")

    client = project.client

    enquiry = (
        project.details
        .filter(detail_type="enquiry")
        .order_by("-created_at")
        .first()
    )

    enquiry_data = enquiry.detail_data if enquiry else {}

    if request.method == "POST":

        try:

            with transaction.atomic():

                # ==================================
                # 01 CLIENT INFORMATION
                # ==================================

                client.client_name = request.POST.get(
                    "client_name", ""
                ).strip()

                client.phone = request.POST.get(
                    "phone", ""
                ).strip()

                client.alternative_phone = request.POST.get(
                    "alternative_phone", ""
                ).strip()

                client.email = request.POST.get(
                    "email", ""
                ).strip() or None

                if not client.client_name or not client.phone:
                    raise ValueError(
                        "Client name and phone are required."
                    )

                client.save()

                # ==================================
                # 02 PROJECT INFORMATION
                # ==================================

                old_status = project.current_status

                project.location = request.POST.get(
                    "location", ""
                ).strip()

                project.google_map_link = request.POST.get(
                    "google_map_link", ""
                ).strip()

                project.project_type = request.POST.get(
                    "project_type", ""
                ).strip()

                area = request.POST.get(
                    "area_sqft", ""
                ).strip()

                project.area_sqft = Decimal(area) if area else None

                # ROOM COUNTS

                project.bedroom_count = int(
                    request.POST.get("bedroom_count") or 0
                )

                project.living_room_count = int(
                    request.POST.get("living_room_count") or 0
                )

                project.kitchen_count = int(
                    request.POST.get("kitchen_count") or 0
                )

                project.bathroom_count = int(
                    request.POST.get("bathroom_count") or 0
                )

                # ==================================
                # 03 PROJECT STATUS
                # ==================================

                status = request.POST.get("current_status")

                valid_statuses = dict(Project.PROJECT_STATUS)

                if status not in valid_statuses:
                    raise ValueError("Invalid project status.")

                project.current_status = status

                # ==================================
                # 04 PROJECT DATES
                # ==================================

                project.enquiry_date = (
                    parse_date(
                        request.POST.get("enquiry_date", "")
                    )
                    or project.enquiry_date
                )

                project.project_start_date = parse_date(
                    request.POST.get("project_start_date", "")
                )

                project.target_handover_date = parse_date(
                    request.POST.get("target_handover_date", "")
                )

                project.actual_handover_date = parse_date(
                    request.POST.get("actual_handover_date", "")
                )

                # ==================================
                # 05 MAP COORDINATES
                # ==================================

                latitude = request.POST.get(
                    "latitude", ""
                ).strip()

                longitude = request.POST.get(
                    "longitude", ""
                ).strip()

                project.latitude = (
                    Decimal(latitude) if latitude else None
                )

                project.longitude = (
                    Decimal(longitude) if longitude else None
                )

                # SAVE PROJECT
                # Project.save() automatically creates
                # ProjectStageHistory when stage changes.

                project.save()

                # Save changed user in stage history

                if old_status != status:

                    history = (
                        project.stage_history
                        .order_by("-history_id")
                        .first()
                    )

                    if history and history.stage == status:

                        history.changed_by = request.user
                        history.save(
                            update_fields=["changed_by"]
                        )

                # ==================================
                # 06 ENQUIRY DETAILS
                # ==================================

                enquiry_data = (
                    enquiry.detail_data.copy()
                    if enquiry else {}
                )

                enquiry_data.update({
                    "property_type": request.POST.get(
                        "property_type", ""
                    ),
                    "budget": request.POST.get(
                        "budget", ""
                    ),
                    "message": request.POST.get(
                        "message", ""
                    ),
                })

                if enquiry:

                    enquiry.detail_data = enquiry_data
                    enquiry.created_by = (
                        enquiry.created_by or request.user
                    )
                    enquiry.save()

                else:

                    ProjectDetail.objects.create(
                        project=project,
                        detail_type="enquiry",
                        detail_data=enquiry_data,
                        created_by=request.user
                    )

                # ==================================
                # 07 ROOM & WORK MANAGEMENT
                # ==================================

                rooms_json = request.POST.get(
                    "rooms_json", "[]"
                )

                rooms_data = json.loads(rooms_json)

                if not isinstance(rooms_data, list):
                    raise ValueError("Invalid room data.")

                for room_data in rooms_data:

                    room_name = room_data.get(
                        "room_name", ""
                    ).strip()

                    if not room_name:
                        raise ValueError("Room name is required.")

                    room_sqft = room_data.get(
                        "area_sqft", 0
                    ) or 0

                    room_id = room_data.get("room_id")

                    if room_id:

                        room = get_object_or_404(
                            ProjectRoom,
                            room_id=room_id,
                            project=project
                        )

                        room.room_name = room_name

                        room.room_type = room_data.get(
                            "room_type", ""
                        )

                        room.area_sqft = Decimal(
                            str(room_sqft)
                        )

                        room.floor = room_data.get(
                            "floor", ""
                        )

                        room.description = room_data.get(
                            "description", ""
                        )

                        room.save()

                    else:

                        room = ProjectRoom.objects.create(
                            project=project,
                            room_name=room_name,
                            room_type=room_data.get(
                                "room_type", ""
                            ),
                            area_sqft=Decimal(
                                str(room_sqft)
                            ),
                            floor=room_data.get("floor", ""),
                            description=room_data.get(
                                "description", ""
                            )
                        )

                    # ==================================
                    # ROOM WORKS
                    # ==================================

                    works_data = room_data.get("works", [])

                    if not isinstance(works_data, list):
                        raise ValueError("Invalid room work data.")

                    for work_data in works_data:

                        work_name = work_data.get(
                            "work_name", ""
                        ).strip()

                        if not work_name:
                            raise ValueError(
                                f"Work name is required in {room_name}."
                            )

                        work_status = work_data.get(
                            "status", "not_started"
                        )

                        valid_work_status = dict(
                            RoomWork.WORK_STATUS
                        )

                        if work_status not in valid_work_status:
                            raise ValueError(
                                "Invalid room work status."
                            )

                        work_sqft = work_data.get(
                            "area_sqft", 0
                        ) or 0

                        work_id = work_data.get("work_id")

                        if work_id:

                            work = get_object_or_404(
                                RoomWork,
                                work_id=work_id,
                                room=room
                            )

                            work.work_name = work_name

                            work.work_description = work_data.get(
                                "work_description", ""
                            )

                            work.area_sqft = Decimal(
                                str(work_sqft)
                            )

                            work.status = work_status

                            work.start_date = parse_date(
                                work_data.get("start_date", "")
                            )

                            work.completed_date = parse_date(
                                work_data.get("completed_date", "")
                            )

                            work.remarks = work_data.get(
                                "remarks", ""
                            )

                            work.save()

                        else:

                            RoomWork.objects.create(
                                room=room,
                                work_name=work_name,
                                work_description=work_data.get(
                                    "work_description", ""
                                ),
                                area_sqft=Decimal(
                                    str(work_sqft)
                                ),
                                status=work_status,
                                start_date=parse_date(
                                    work_data.get("start_date", "")
                                ),
                                completed_date=parse_date(
                                    work_data.get("completed_date", "")
                                ),
                                remarks=work_data.get(
                                    "remarks", ""
                                )
                            )

            messages.success(
                request,
                "Project updated successfully!"
            )

            return redirect("owner_projects")

        except (
            ValueError,
            InvalidOperation,
            TypeError
        ) as error:

            messages.error(
                request,
                f"Unable to update project: {error}"
            )

    # ==================================
    # GET DATA
    # ==================================

    rooms = (
        ProjectRoom.objects
        .filter(project=project)
        .prefetch_related("works")
        .order_by("room_id")
    )

    stage_history = (
        project.stage_history
        .select_related("changed_by")
        .order_by("changed_at", "history_id")
    )

    context = {
        "project": project,
        "client": client,
        "enquiry_data": enquiry_data,
        "status_choices": Project.PROJECT_STATUS,
        "rooms": rooms,
        "stage_history": stage_history,
    }

    return render(request,"owner/edit_project.html",context)


@login_required
def project_update(request, project_id):

    project = get_object_or_404(
        Project.objects.select_related("client"),
        project_id=project_id
    )

    # ----------------------------------------
    # OWNER PERMISSION
    # ----------------------------------------
    profile = getattr(request.user, "userprofile", None)

    if not profile or not profile.is_owneruser:
        messages.error(
            request,
            "You don't have permission to edit this project."
        )
        return redirect("login")

    client = project.client

    # ----------------------------------------
    # PROJECT PROGRESS
    # ----------------------------------------
    progress_map = {
        "enquiry": 1,
        "quotation": 8,
        "site_visit": 25,
        "payment": 50,
        "3d_design": 63,
        "material_selection": 75,
        "execution": 90,
        "handover": 100,
    }

    # ----------------------------------------
    # LATEST ENQUIRY DETAILS
    # ----------------------------------------
    enquiry = (
        project.details
        .filter(detail_type="enquiry")
        .order_by("-created_at")
        .first()
    )

    enquiry_data = (
        enquiry.detail_data.copy()
        if enquiry and enquiry.detail_data
        else {}
    )

    # ----------------------------------------
    # POST UPDATE
    # ----------------------------------------
    if request.method == "POST":
        try:
            with transaction.atomic():

                # CLIENT DETAILS
                client.client_name = request.POST.get(
                    "client_name", ""
                ).strip()
                client.phone = request.POST.get(
                    "phone", ""
                ).strip()
                client.alternative_phone = request.POST.get(
                    "alternative_phone", ""
                ).strip()
                client.email = request.POST.get(
                    "email", ""
                ).strip() or None

                if not client.client_name or not client.phone:
                    raise ValueError(
                        "Client name and phone are required."
                    )

                client.save()

                # PROJECT DETAILS
                project.project_code = request.POST.get(
                    "project_code", project.project_code
                ).strip()
                project.location = request.POST.get(
                    "location", ""
                ).strip()
                project.google_map_link = request.POST.get(
                    "google_map_link", ""
                ).strip()
                project.project_type = request.POST.get(
                    "project_type", ""
                ).strip()

                area = request.POST.get("area_sqft", "").strip()
                project.area_sqft = Decimal(area) if area else None

                # ROOM COUNTS
                project.bedroom_count = int(
                    request.POST.get("bedroom_count") or 0
                )
                project.living_room_count = int(
                    request.POST.get("living_room_count") or 0
                )
                project.kitchen_count = int(
                    request.POST.get("kitchen_count") or 0
                )
                project.bathroom_count = int(
                    request.POST.get("bathroom_count") or 0
                )

                # PROJECT STATUS
                status = request.POST.get("current_status")
                valid_statuses = dict(Project.PROJECT_STATUS)

                if status not in valid_statuses:
                    raise ValueError("Invalid project status.")

                project.current_status = status

                # PROJECT DATES
                project.enquiry_date = (
                    parse_date(request.POST.get("enquiry_date", ""))
                    or project.enquiry_date
                )
                project.project_start_date = parse_date(
                    request.POST.get("project_start_date", "")
                )
                project.target_handover_date = parse_date(
                    request.POST.get("target_handover_date", "")
                )
                project.actual_handover_date = parse_date(
                    request.POST.get("actual_handover_date", "")
                )

                # MAP COORDINATES
                latitude = request.POST.get("latitude", "").strip()
                longitude = request.POST.get("longitude", "").strip()

                project.latitude = Decimal(latitude) if latitude else None
                project.longitude = Decimal(longitude) if longitude else None

                # Save project. Your Project.save() stage-history logic
                # should create a history row when current_status changes.
                project.save()

                # ENQUIRY JSON DETAILS
                enquiry_data = (
                    enquiry.detail_data.copy()
                    if enquiry and enquiry.detail_data
                    else {}
                )
                enquiry_data.update({
                    "property_type": request.POST.get("property_type", ""),
                    "budget": request.POST.get("budget", ""),
                    "message": request.POST.get("message", ""),
                })

                if enquiry:
                    enquiry.detail_data = enquiry_data
                    enquiry.save()
                else:
                    ProjectDetail.objects.create(
                        project=project,
                        detail_type="enquiry",
                        detail_data=enquiry_data,
                        created_by=request.user
                    )

            messages.success(request, "Project updated successfully!")
            return redirect("owner_projects")

        except (ValueError, InvalidOperation, TypeError) as error:
            messages.error(
                request,
                f"Unable to update project: {error}"
            )

    # ----------------------------------------
    # PROJECT ROOMS + ROOM WORKS
    # ----------------------------------------
    rooms = (
        project.rooms
        .prefetch_related("works")
        .order_by("room_id")
    )

    project_rooms_data = []

    for room in rooms:
        room_works_data = []

        for work in room.works.all():
            room_works_data.append({
                "work_id": work.work_id,
                "work_name": work.work_name,
                "work_name_display": (work.work_name or "").replace("_", " ").title(),
                "work_description": work.work_description,
                "area_sqft": (
                    str(work.area_sqft)
                    if work.area_sqft is not None else "0"
                ),
                "status": work.status,
                "start_date": (
                    work.start_date.isoformat()
                    if work.start_date else None
                ),
                "completed_date": (
                    work.completed_date.isoformat()
                    if work.completed_date else None
                ),
                "remarks": work.remarks,
            })

        project_rooms_data.append({
            "room_id": room.room_id,
            "room_name": room.room_name,
            "room_type": room.room_type,
            "area_sqft": (
                str(room.area_sqft)
                if room.area_sqft is not None else "0"
            ),
            "floor": room.floor,
            "description": room.description,
            "works_count": len(room_works_data),
            "completed_works": sum(
                1 for work in room_works_data
                if work["status"] == "completed"
            ),
            "works": room_works_data,
        })

    # ----------------------------------------
    # PROJECT STAGE HISTORY + KEY MILESTONES
    # ----------------------------------------
    stage_history = list(
        project.stage_history.order_by("changed_at")
    )

    # Keep the latest changed_at for each stage.
    stage_date_map = {}
    for history in stage_history:
        stage_date_map[history.stage] = history.changed_at

    stage_milestones = []

    for stage_value, stage_label in Project.PROJECT_STATUS:
        # Enquiry always uses the project's creation timestamp.
        if stage_value == "enquiry":
            changed_at = project.created_at
        else:
            # Every other stage uses its actual history timestamp only.
            changed_at = stage_date_map.get(stage_value)

        stage_milestones.append({
            "stage": stage_value,
            "label": stage_label,
            "changed_at": changed_at,
            "is_current": stage_value == project.current_status,
            "is_completed": (
                changed_at is not None
                and stage_value != project.current_status
            ),
        })

    # ----------------------------------------
    # FINAL CONTEXT
    # ----------------------------------------
    progress = progress_map.get(project.current_status, 0)

    context = {
        "project": project,
        "client": client,
        "progress": progress,
        "enquiry_data": enquiry_data,
        "status_choices": Project.PROJECT_STATUS,

        # Project -> Rooms -> Works
        "project_rooms_data": project_rooms_data,
        "total_rooms": len(project_rooms_data),
        "total_works": sum(
            len(room["works"]) for room in project_rooms_data
        ),

        # Stage history and milestones
        "stage_history": stage_history,
        "stage_milestones": stage_milestones,
    }

    return render(
        request,
        "owner/project_update.html",
        context
    )

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
        last_project = Project.objects.filter(
            project_code__startswith="IBK-"
        ).order_by("-project_id").first()

        if last_project:
            last_number = int(last_project.project_code.split("-")[1])
            next_number = max(last_number + 1, 9)
        else:
            next_number = 9

        project_code = f"IBK-{next_number:04d}"

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
