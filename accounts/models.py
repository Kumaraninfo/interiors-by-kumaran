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

    # PROJECT FINANCIAL DETAILS
    project_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    project_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
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

    enquiry_date = models.DateField(
        default=timezone.localdate
    )

    project_start_date = models.DateField(
        null=True,
        blank=True
    )

    target_handover_date = models.DateField(
        null=True,
        blank=True
    )

    actual_handover_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"

    def save(self, *args, **kwargs):

        is_new = self.pk is None
        old_status = None

        if not is_new:
            old_status = (
                Project.objects
                .filter(pk=self.pk)
                .values_list("current_status", flat=True)
                .first()
            )

        if not self.project_code:

            last_project = (
                Project.objects
                .filter(project_code__startswith="IBK-")
                .order_by("-project_id")
                .first()
            )

            if last_project:
                last_number = int(
                    last_project.project_code.split("-")[1]
                )
                next_number = last_number + 1
            else:
                next_number = 1

            self.project_code = f"IBK-{next_number:04d}"

        super().save(*args, **kwargs)

        if is_new:
            ProjectStageHistory.objects.create(
                project=self,
                stage="enquiry"
            )

        elif old_status != self.current_status:
            ProjectStageHistory.objects.create(
                project=self,
                stage=self.current_status
            )

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



class ProjectRoom(models.Model):

    room_id = models.BigAutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="rooms"
    )

    room_name = models.CharField(max_length=100)

    room_type = models.CharField(
        max_length=100,
        blank=True
    )

    area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    floor = models.CharField(
        max_length=50,
        blank=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_rooms"
        ordering = ["room_id"]

    def __str__(self):
        return f"{self.project.project_code} - {self.room_name}"



class RoomWork(models.Model):

    WORK_STATUS = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    work_id = models.BigAutoField(primary_key=True)

    room = models.ForeignKey(
        ProjectRoom,
        on_delete=models.CASCADE,
        related_name="works"
    )

    work_name = models.CharField(
        max_length=150
    )

    work_description = models.TextField(
        blank=True
    )

    area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=30,
        choices=WORK_STATUS,
        default="not_started"
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    completed_date = models.DateField(
        null=True,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "room_works"
        ordering = ["work_id"]

    def __str__(self):
        return f"{self.room.room_name} - {self.work_name}"



class ProjectStageHistory(models.Model):

    history_id = models.BigAutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="stage_history"
    )

    stage = models.CharField(
        max_length=50,
        choices=Project.PROJECT_STATUS
    )

    changed_at = models.DateTimeField(
        default=timezone.now
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_stage_changes"
    )

    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "project_stage_history"
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.project.project_code} - {self.get_stage_display()}"



class ProjectPayment(models.Model):

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
    ]

    PAYMENT_MODES = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("cheque", "Cheque"),
        ("card", "Card"),
        ("other", "Other"),
    ]

    payment_id = models.BigAutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="payment_schedule"
    )

    milestone = models.CharField(max_length=150)

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    payment_mode = models.CharField(
        max_length=30,
        choices=PAYMENT_MODES,
        blank=True
    )

    transaction_reference = models.CharField(
        max_length=150,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_payments"
        ordering = ["payment_id"]

    def __str__(self):
        return f"{self.project.project_code} - {self.milestone}"
