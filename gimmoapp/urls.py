from django.contrib import admin
from django.urls import path,include,re_path
from django.views.static import serve
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gimmo.urls')),
    #path('', include('pwa.urls')),
    re_path(r'^media/(?P<path>.*)$',serve,{'document_root':settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "gimmo.views.error_404"
handler500 = "gimmo.views.error_500"