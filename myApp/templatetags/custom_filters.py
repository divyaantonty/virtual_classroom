from django import template
from django.db.models import Avg, Max, Count

register = template.Library()

@register.filter
def filter_grades(grades, course):
    """Filter grades for a specific course"""
    return [g for g in grades if g.question.quiz.course == course]

@register.filter
def average_score(grades):
    """Calculate average score from grades"""
    if not grades:
        return 0
    return sum(g.percentage for g in grades) / len(grades)

@register.filter
def quiz_stats(grades, course):
    """Get quiz statistics for a course"""
    course_grades = [g for g in grades if g.question.quiz.course == course]
    if not course_grades:
        return {'passed': 0, 'failed': 0, 'best_score': 0}
    
    passed = sum(1 for g in course_grades if g.percentage >= 50)
    failed = len(course_grades) - passed
    best_score = max((g.percentage for g in course_grades), default=0)
    
    return {
        'passed': passed,
        'failed': failed,
        'best_score': best_score
    }

@register.filter
def get_class_name(obj):
    return obj.__class__.__name__

@register.filter
def multiply(value, arg):
    return float(value) * float(arg) 