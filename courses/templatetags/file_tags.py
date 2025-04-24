# templatetags/file_tags.py
from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """
    Check if the value ends with the specified suffix.
    """
    return value.lower().endswith(arg.lower())

@register.filter
def split(value, arg):
    """
    Split the value by the specified separator.
    """
    return value.split(arg)

@register.filter
def pop(value):
    """
    Return the last element of a list.
    """
    if isinstance(value, list):
        return value[-1]
    return ''