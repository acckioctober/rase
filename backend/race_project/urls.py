"""
URL configuration for race_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('users/', include('users.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django_email_verification import urls as email_urls


from django.conf import settings
from race.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('email/', include(email_urls), name='email_verification'),
    path('', include('race.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

# handler404 = page_not_found

admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Организация любительских забегов"
