from django import template

register = template.Library()


@register.filter
def format_duration(duration):
    if not duration:
        return None
    seconds = duration.total_seconds()
    assert seconds < 3600
    mm, ss = divmod(seconds, 60)
    return "%dmin %ds" % (mm, ss)
