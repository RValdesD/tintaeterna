from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("upload/<int:upload_id>/presentation/", views.edit_story_presentation, name="edit_story_presentation"),
    path("stories/<int:upload_id>/cover/", views.story_cover, name="story_cover"),
    path("profile/", views.my_profile, name="my_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/picture/edit/", views.edit_profile_picture, name="edit_profile_picture"),
    path("authors/<int:user_id>/picture/", views.profile_picture, name="profile_picture"),
    path("authors/<int:user_id>/", views.public_profile, name="profile"),
    path("authors/demo/<str:author>/", views.demo_profile, name="demo_profile"),
    path("bookmarks/", views.bookmarks, name="bookmarks"),
    path("read/<int:upload_id>/bookmark/", views.save_bookmark, name="save_bookmark"),
    path("read/<int:upload_id>/bookmark/delete/", views.delete_bookmark, name="delete_bookmark"),
    path("read/<int:upload_id>/", views.reader, name="reader"),
    path("read/<int:upload_id>/file/", views.reader_file, name="reader_file"),
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
