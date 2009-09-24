from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'admin-required/', 'tests.views.admin_required_view'),
)
