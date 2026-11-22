
from django.contrib import admin

from .models import (
    UserProfile,
    Client,
    Employee,
    Project,
    ProjectDetail,
    ProjectRoom,
    RoomWork,
    ProjectStageHistory
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


# ==================================
# PROJECT ROOM ADMIN
# ==================================

@admin.register(ProjectRoom)
class ProjectRoomAdmin(admin.ModelAdmin):

    list_display = (
        "room_id",
        "project",
        "room_name",
        "room_type",
        "area_sqft",
    )

    search_fields = (
        "room_name",
        "project__project_code",
    )


# ==================================
# ROOM WORK ADMIN
# ==================================

@admin.register(RoomWork)
class RoomWorkAdmin(admin.ModelAdmin):

    list_display = (
        "work_id",
        "room",
        "work_name",
        "area_sqft",
        "status",
        "start_date",
        "completed_date",
    )

    list_filter = ("status",)

    search_fields = (
        "work_name",
        "room__room_name",
        "room__project__project_code",
    )


# ==================================
# PROJECT STAGE HISTORY ADMIN
# ==================================

@admin.register(ProjectStageHistory)
class ProjectStageHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "history_id",
        "project",
        "stage",
        "changed_at",
        "changed_by",
    )

    list_filter = ("stage", "changed_at")

    search_fields = (
        "project__project_code",
        "remarks",
    )

    readonly_fields = ("changed_at",)
