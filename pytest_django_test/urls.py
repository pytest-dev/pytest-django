try:
    from django.conf.urls import patterns  # Django >1.4
except ImportError:
    from django.conf.urls.defaults import patterns  # Django 1.3

urlpatterns = patterns(
    '',
    (r'^item_count/$', 'pytest_django_test.app.views.item_count'),
    (r'^admin-required/$', 'pytest_django_test.app.views.admin_required_view'),
)
