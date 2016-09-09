"""@@SITENAME@@ URL Configuration"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView
@@URL_IMPORTS@@

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
@@URLS@@
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
    )
