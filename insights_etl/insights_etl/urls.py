"""
Definition of urls for insights_etl.
"""

from datetime import datetime
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from app.forms import BootstrapAuthenticationForm
import app.views as views

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin
admin.autodiscover()

from django.contrib import auth

#params={'plugin': ModelSearchPlugin(MyModel), 'base_template': 'search.html'}
params={'plugin': '', 'base_template': 'search.html'}

import app.models as models
import app.views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', app.views.home, name='home'),

    url(r'^load', app.views.load_view, name='load'),
    url(r'^fmi_admin', app.views.fmi_admin_view, name='fmi_admin'),

    url(r'^contact$', app.views.contact, name='contact'),
    url(r'^about', app.views.about, name='about'),

    # Registration URLs
    url(r'^accounts/register/$', views.register, name='register'),
    url(r'^accounts/register_complete/$', views.registrer_complete, name='register_complete'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', admin.site.urls),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)