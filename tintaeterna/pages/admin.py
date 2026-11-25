from django.contrib import admin
from .models import StoryUpload, Tag

# Register your models here.
admin.site.register(Tag)
admin.site.register(StoryUpload)
