from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^/$', views.index, name='index'),
    url(r'^(?i)/connectToQuickbooks/?$', views.connectToQuickbooks, name='connectToQuickbooks'),
    url(r'^(?i)/signInWithIntuit/?$', views.signInWithIntuit, name='signInWithIntuit'),
    url(r'^(?i)/getAppNow/?$', views.getAppNow, name='getAppNow'),
    url(r'^(?i)/authCodeHandler/?$', views.authCodeHandler, name='authCodeHandler'),
    url(r'^(?i)/disconnect/?$', views.disconnect, name='disconnect'),
    url(r'^(?i)/apiCall/?$', views.apiCall, name='apiCall'),
    url(r'^(?i)/newInvoice/?$', views.newInvoice, name='newInvoice'),
    url(r'^(?i)/oneInvoice/?$', views.newInvoice, name='oneInvoice'),
    url(r'^(?i)/newCustomer/?$', views.newCustomer, name='newCustomer'),
    url(r'^(?i)/oneCustomer/?$', views.oneCustomer, name='oneCustomer'),
    url(r'^(?i)/newItem/?$', views.newItem, name='newItem'),
    url(r'^(?i)/oneItem/?$', views.oneItem, name='onwItem'),
    url(r'^(?i)/showAllItem/?$', views.allItem, name='allItem'),
    url(r'^(?i)/showAllCustomer/?$', views.allCustomer, name='allCustomer'),
    url(r'^(?i)/connected/?$', views.connected, name='connected'),
    url(r'^(?i)/refreshTokenCall/?$', views.refreshTokenCall, name='refreshTokenCall')
]