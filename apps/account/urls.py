from django.conf.urls import include, url
from rest_framework import routers
from apps.account import views

router = routers.DefaultRouter()
router.register(r'follows', views.FollowViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls))
]
