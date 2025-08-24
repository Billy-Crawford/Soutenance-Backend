#config/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),  # 👈 Doit bien être là

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login pour obtenir access + refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # rafraîchir token

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
