from django.contrib import admin
from django.urls import path

from club_bot.views import simple_payment

urlpatterns = [
    path('api/v1', simple_payment),
    path('admin/', admin.site.urls),
]
