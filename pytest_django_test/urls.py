from django.urls import path

from .app import views


urlpatterns = [
    path("item_count/", views.item_count),
    path("admin-required/", views.admin_required_view),
]
