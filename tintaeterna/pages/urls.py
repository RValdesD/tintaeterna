from django.urls import path
from . import comment_views
from . import views, moderation_views, catalog_views, profile_views, story_edit

app_name = "pages"

urlpatterns = [
    path("comments/reader/<int:comment_id>/delete/", comment_views.delete_reader_comment, name="delete_reader_comment"),
    path("comments/profile/<int:comment_id>/delete/", comment_views.delete_profile_comment, name="delete_profile_comment"),
    path("works/<int:upload_id>/edit/", story_edit.edit_story, name="edit_story"),
    path("settings/", profile_views.settings_page, name="account_settings"),
    path("authors/<int:user_id>/banner/", profile_views.banner, name="profile_banner"),
    path("recent/", catalog_views.recent, name="recent"),
    path("popular/", catalog_views.popular, name="popular"),
    path("moderation/", moderation_views.dashboard, name="moderation_dashboard"),
    path("moderation/<str:kind>/<int:target_id>/", moderation_views.action, name="moderation_action"),
    path("account/notices/", moderation_views.notices, name="moderation_notices"),
    path("works/<int:upload_id>/", views.work_detail, name="work_detail"),
    path("works/sample/<int:sample_id>/", views.sample_work, name="sample_work"),
    path("upload/<int:upload_id>/presentation/", story_edit.edit_story, name="edit_story_presentation"),
    path("stories/<int:upload_id>/cover/", views.story_cover, name="story_cover"),
    path("profile/", views.my_profile, name="my_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/picture/edit/", views.edit_profile_picture, name="edit_profile_picture"),
    path("authors/<int:user_id>/picture/", views.profile_picture, name="profile_picture"),
    path("authors/<int:user_id>/", profile_views.public_profile, name="profile"),
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
