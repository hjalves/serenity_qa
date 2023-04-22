import logging

from django.conf import settings

from serenity_qa.common.models import Notification


logger = logging.getLogger(__name__)


def send_notification(text, username=None, channel=None, icon_emoji=None):
    logger.debug("Sending notification: %s", text)
    notification = Notification.objects.create(
        username=username or settings.SLACK_USERNAME,
        channel=channel or settings.SLACK_CHANNEL,
        icon_emoji=icon_emoji or "",
        text=text,
    )
    if settings.DEBUG:
        notification.send()
    else:
        notification.send_async()
