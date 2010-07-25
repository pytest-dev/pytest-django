from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'admin-required/', 'tests.views.admin_required_view'),
)
