from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    (r'^item_count/$', 'pytest_django_test.app.views.item_count'),
    (r'^admin-required/$', 'pytest_django_test.app.views.admin_required_view'),
)
