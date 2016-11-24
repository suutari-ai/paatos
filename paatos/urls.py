from django.conf.urls import include, url
from django.contrib import admin

from decisions import urls_v1

urlpatterns = [
    url(r'^v1/', include(urls_v1)),
    url(r'^admin/', admin.site.urls),
]
