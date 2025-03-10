from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def map_event_ids(registrations):
    """Returns a list of event IDs from registrations"""
    return [reg.event.id for reg in registrations]

@register.filter
def is_registered(event, registered_events):
    """Check if event is in registered events"""
    return event.id in [reg.event.id for reg in registered_events]

@register.filter
def format_event_time(event):
    """Format event time nicely"""
    return event.start_time.strftime('%I:%M %p')

@register.filter
def get_event_status(event, now):
    current_date = now.date()
    start_date = event.start_time.date()
    end_date = event.end_time.date()
    
    if current_date < start_date:
        return 'upcoming'
    elif current_date > end_date:
        return 'ended'
    else:
        return 'ongoing' 