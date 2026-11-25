from django import template
from pages.comment_views import can_delete_comment
register = template.Library()
register.filter('can_delete_comment', can_delete_comment)
