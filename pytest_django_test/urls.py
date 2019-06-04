from django.conf.urls import url

from .app import views

urlpatterns = [
    url(r"^item_count/$", views.item_count),
    url(r"^admin-required/$", views.admin_required_view),
]
