from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from .views import (
    VehicleViewSet,
    TripViewSet,
    DriverViewSet,
    RatingViewSet,
    HomeView,
    LoginView,
    FirebaseLoginView
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login', LoginView.as_view(), name='login'),
    path('firebase', FirebaseLoginView.as_view(), name="firebase_login"),
    path('api/', include(router.urls)),
    path('api-token-auth/', views.obtain_auth_token),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify')
]
