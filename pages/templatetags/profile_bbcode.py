import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
register = template.Library()
TAGS = {"b": "strong", "i": "em", "u": "u", "s": "s", "quote": "blockquote", "code": "code"}


@register.filter
def bbcode(value):
    # Only fixed tags are emitted; every piece of user text is escaped.
    parts = re.split(r"(\[/?(?:b|i|u|s|quote|code)\])", str(value or ""), flags=re.I)
    result, stack = [], []
    for part in parts:
        token = part.lower()
        if token.startswith("[") and token.endswith("]"):
            closing = token.startswith("[/")
            name = token[2:-1] if closing else token[1:-1]
            if name in TAGS and not closing and len(stack) < 20:
                stack.append(name)
                result.append(f"<{TAGS[name]}>")
                continue
            if name in TAGS and closing and stack and stack[-1] == name:
                stack.pop()
                result.append(f"</{TAGS[name]}>")
                continue
        result.append(str(escape(part)))
    result.extend(f"</{TAGS[name]}>" for name in reversed(stack))
    return mark_safe("".join(result))
