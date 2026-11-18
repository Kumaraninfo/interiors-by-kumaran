
from django.contrib import admin
from .models import (
    UserProfile,
    Client,
    Employee,
    Project,
    ProjectDetail
)


# ==================================
# USER PROFILE ADMIN
# ==================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "is_owneruser",
        "is_manageruser",
        "is_sitemanageruser",
        "is_clientuser",
        "phone",
    )

    list_filter = (
        "is_owneruser",
        "is_manageruser",
        "is_sitemanageruser",
        "is_clientuser",
    )


# ==================================
# CLIENT ADMIN
# ==================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    list_display = (
        "client_id",
        "client_name",
        "phone",
        "email",
        "created_at",
    )

    search_fields = (
        "client_name",
        "phone",
        "email",
    )


# ==================================
# EMPLOYEE ADMIN
# ==================================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        "employee_id",
        "employee_name",
        "phone",
        "email",
        "role",
        "is_active",
    )

    list_filter = ("role", "is_active")

    search_fields = (
        "employee_name",
        "phone",
        "email",
    )


# ==================================
# PROJECT ADMIN
# ==================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "project_id",
        "project_code",
        "client",
        "location",
        "project_type",
        "current_status",
        "created_at",
    )

    list_filter = (
        "current_status",
        "project_type",
    )

    search_fields = (
        "project_code",
        "location",
        "client__client_name",
    )


# ==================================
# PROJECT DETAILS ADMIN
# ==================================

@admin.register(ProjectDetail)
class ProjectDetailAdmin(admin.ModelAdmin):

    list_display = (
        "detail_id",
        "project",
        "detail_type",
        "created_at",
    )

    list_filter = ("detail_type",)

    search_fields = ("project__project_code",)
