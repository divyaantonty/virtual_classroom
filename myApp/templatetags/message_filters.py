from django import template

register = template.Library()

@register.filter
def unread_count(messages):
    return len([m for m in messages if not m.is_read and m.message_type == 'teacher_to_parent'])

@register.filter
def sent_count(messages):
    return len([m for m in messages if m.message_type == 'parent_to_teacher'])