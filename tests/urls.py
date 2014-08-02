from .compat import patterns, url

urlpatterns = patterns(
    '',
    url(r'admin-required/', 'tests.views.admin_required_view', name='admin-required'),
)
