from django import template
from pages.moderation import is_moderator
register = template.Library()
register.filter("is_moderator", is_moderator)
