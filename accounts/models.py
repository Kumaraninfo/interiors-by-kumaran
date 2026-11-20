from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    is_owneruser = models.BooleanField(default=False)

    is_manageruser = models.BooleanField(default=False)

    is_sitemanageruser = models.BooleanField(default=True)

    is_clientuser = models.BooleanField(default=False)

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    def __str__(self):
        return self.user.username




class Client(models.Model):
    client_id = models.BigAutoField(primary_key=True)

    client_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    client_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=15)
    alternative_phone = models.CharField(
        max_length=15, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clients"

    def __str__(self):
        return self.client_name

class Employee(models.Model):
    employee_id = models.BigAutoField(primary_key=True)
    employee_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=150, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "employees"

    def __str__(self):
        return self.employee_name



class Project(models.Model):

    PROJECT_STATUS = [
        ("enquiry", "Enquiry"),
        ("quotation", "Quotation"),
        ("site_visit", "Site Visit"),
        ("payment", "Payment"),
        ("3d_design", "3D Design"),
        ("material_selection", "Material Selection"),
        ("execution", "Execution"),
        ("handover", "Handover"),
    ]

    project_id = models.BigAutoField(primary_key=True)

    project_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="projects"
    )

    location = models.CharField(max_length=150, blank=True)
    google_map_link = models.TextField(blank=True)

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    project_type = models.CharField(max_length=100, blank=True)

    area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    bedroom_count = models.IntegerField(default=0)
    living_room_count = models.IntegerField(default=0)
    kitchen_count = models.IntegerField(default=0)
    bathroom_count = models.IntegerField(default=0)

    current_status = models.CharField(
        max_length=50,
        choices=PROJECT_STATUS,
        default="enquiry"
    )

    enquiry_date = models.DateField(default=timezone.localdate)
    project_start_date = models.DateField(null=True, blank=True)
    target_handover_date = models.DateField(null=True, blank=True)
    actual_handover_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"

    def save(self, *args, **kwargs):

        if not self.project_code:

            last_project = Project.objects.filter(
                project_code__startswith="IBK-"
            ).order_by("-project_id").first()

            if last_project:
                last_number = int(
                    last_project.project_code.split("-")[1]
                )
                next_number = last_number + 1
            else:
                next_number = 1

            self.project_code = f"IBK-{next_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.project_code


class ProjectDetail(models.Model):

    DETAIL_TYPES = [
        ("enquiry", "Client Enquiry"),
        ("room", "Room"),
        ("scope", "Project Scope"),
        ("assignment", "Project Assignment"),
        ("status_history", "Status History"),
        ("site_visit", "Site Visit"),
        ("quotation", "Quotation"),
        ("payment", "Payment"),
        ("design", "Design"),
        ("material", "Material"),
        ("execution_task", "Execution Task"),
        ("document", "Project Document"),
        ("handover", "Handover"),
    ]

    detail_id = models.BigAutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="details"
    )

    detail_type = models.CharField(
        max_length=50,
        choices=DETAIL_TYPES
    )

    detail_data = models.JSONField(default=dict)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_details"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.project_code} - {self.detail_type}"
