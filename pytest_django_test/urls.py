from django.conf.urls import url

from .app import views
from .compat import patterns

urlpatterns = patterns(
    "",
    url(r"^item_count/$", views.item_count),
    url(r"^admin-required/$", views.admin_required_view),
)
