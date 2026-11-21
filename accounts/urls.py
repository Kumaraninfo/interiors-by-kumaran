from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),
    path("client/profile/", views.client_profile, name="client_profile"),
    path("owner/dashboard/",views.owner_dashboard,name="owner_dashboard"),
    path("manager/dashboard/",views.manager_dashboard,name="manager_dashboard"),
    path('projects/<int:project_id>/update-status/',views.update_project_status,name='update_project_status'),
    path("projects/<int:project_id>/edit/",views.edit_project,name="edit_project"),
    path('owner/project/<int:project_id>/update/',views.project_update,name='project_update'),
    path('owner/projects/',views.owner_projects,name='owner_projects'),
    path('owner/team/', views.owner_team, name='owner_team'),
    path('owner/project-map/', views.owner_project_map, name='projects_map'),
    path("sitepm/dashboard/",views.sitepm_dashboard,name="sitepm_dashboard"),
    path("client/dashboard/",views.client_dashboard,name="client_dashboard"),
    path("client-booking/",views.client_booking,name="client_booking"),

    path("owner/newproject/", views.owner_projects, name="newproject"),

]