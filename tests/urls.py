from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    (r'admin-required/', 'tests.views.admin_required_view'),
)
