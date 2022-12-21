import datetime

from django.contrib import admin
from django.contrib.admin.helpers import AdminForm
from django.utils import timezone
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions

from .admin_realtime import ModelAdminRealtime, autoupdate
from .forms import DumpDataForm
from .models import Job
from .utils import get_job_log
from ..admin_actions.decorators import action_view


@admin.register(Job)
class JobAdmin(DjangoObjectActions, ModelAdminRealtime):
    change_form_template = "admin/common/job/change_form.html"
    autorefresh = 2
    search_fields = ("task_name", "description")
    list_filter = ("task_name", "state")
    list_display = (
        "__str__",
        "result_progress",
        "elapsed",
        "created_at",
    )

    readonly_fields = (
        "task_id",
        "task_name",
        "description",
        "message",
        "_state",
        "result_info",
        "created_at",
        "started_at",
        "finished_at",
        "elapsed",
        "result_progress",
    )
    fieldsets = (
        (None, {"fields": ("description", "result_progress", "elapsed", "message")}),
        (
            "Details",
            {
                "fields": (
                    "task_id",
                    "task_name",
                    "_state",
                    "created_at",
                    "started_at",
                    "finished_at",
                    "result_info",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Job log", {"fields": ("job_log",), "classes": ("collapse",)}),
    )
    changelist_actions = ("dumpdata",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def result_info(self, obj):
        return obj.result_info() or "-"

    @autoupdate(polling=2000, condition=lambda obj: obj.state not in Job.READY_STATES)
    def elapsed(self, obj):
        if obj.started_at is None:
            return "-"
        if not obj.finished_at and obj.realtime_state() == "PENDING":
            return "-"
        to_time = obj.finished_at or timezone.now()
        td = to_time - obj.started_at
        secs = td.total_seconds()
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return "%02d:%02d:%02d" % (hours, mins, secs)
        return "%02d:%02d" % (mins, secs)

    @autoupdate(polling=2000, condition=lambda obj: obj.state not in Job.READY_STATES)
    def result_progress(self, obj):
        state = obj.realtime_state()
        if state in Job.READY_STATES:
            return Job.READY_STATES[state]

        value = obj.progress_percentage()
        return format_html(
            '<progress max=100 {value} style="width: 250px"></progress> '
            "<span>{text}</span>",
            value="value={}".format(value) if value is not None else "",
            text="{} %".format(value) if value is not None else "",
        )

    result_progress.short_description = "Progress"

    @autoupdate(polling=2000, condition=lambda obj: obj.state not in Job.READY_STATES)
    def message(self, obj):
        return obj.progress_message() or "-"

    message.short_description = "Message"

    def _state(self, obj):
        return format_html(
            '<span id="state-job-{id}">{state}</span>',
            id=obj.id,
            state=obj.realtime_state(),
        )

    _state.short_description = "state"

    def job_log(self, obj):
        def log_format(e):
            levelname, message = e["levelname"], e["message"]
            dt = datetime.datetime.fromtimestamp(e["created"])
            dt = dt.isoformat(" ", timespec="milliseconds")
            return f"{dt} [{levelname}] {message}"

        job_log = get_job_log(obj.task_id)
        return "\n".join(log_format(e) for e in job_log)

    @action_view()
    def dumpdata(self, request, queryset):
        data = request.GET
        form = DumpDataForm(initial=data)

        fieldsets = [(None, {"fields": ["model_name", "arguments"]})]
        admin_form = AdminForm(form, fieldsets, {})
        if request.method == "POST":
            form = DumpDataForm(data=request.POST)
            if form.is_valid():
                print(form.cleaned_data)
            admin_form = None

        return {
            "subtitle": "Choose a model to dump data from",
            "adminform": admin_form,
            "content": "Will dump data",
        }
