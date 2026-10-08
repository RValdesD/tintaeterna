from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload, name="upload"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),

    path(
    "upload/<int:upload_id>/delete/",
    views.delete_upload,
    name="delete_upload",
    ),

    path("logout/", views.logout_page, name="logout"),
]