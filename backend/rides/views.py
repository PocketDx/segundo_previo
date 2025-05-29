import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.views.generic import TemplateView

import rest_framework
from rest_framework import (
    decorators,
    mixins,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from rest_framework.authtoken.models import Token

from rest_framework_simplejwt.tokens import RefreshToken

from django_filters.rest_framework import DjangoFilterBackend

from .models import Rating, Trip, Vehicle
from .serializers import (
    RatingSerializer,
    TripSerializer,
    UserSerializer,
    VehicleSerializer,
)

User = get_user_model()


class HomeView(TemplateView):
    """
    Vista de inicio de la aplicación.
    """

    template_name = "rides/home.html"

class FirebaseLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # 1) Leer el ID token de Firebase del body
        try:
            payload = request.data
        except Exception:
            return response.Response(
                {"detail": "Invalid request body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        id_token = payload.get("id_token")
        if not id_token:
            return response.Response(
                {"detail": "Field 'id_token' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Verificar el token con Firebase Admin
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except firebase_auth.ExpiredIdTokenError:
            return response.Response(
                {"detail": "Firebase ID token has expired."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except firebase_auth.InvalidIdTokenError:
            return response.Response(
                {"detail": "Invalid Firebase ID token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return response.Response(
                {"detail": f"Error verifying ID token: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Obtener o crear usuario Django
        uid = decoded.get("uid")
        email = decoded.get("email", "")
        user, created = User.objects.get_or_create(
            username=uid,
            defaults={"email": email}
        )
        if not created and email and user.email != email:
            user.email = email
            user.save(update_fields=["email"])

        # 4) Generar tokens JWT con Simple JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 5) Devolver los tokens
        return response.Response({
            "access": access_token,
            "refresh": refresh_token
        }, status=status.HTTP_200_OK)
        
class LoginView(TemplateView):
    template_name="rides/login.html"

class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de vehículos.
    """

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar trips.

    Soporta filtro por driver con ?driver=<id>.
    """

    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["driver"]

    @decorators.action(methods=["POST"], detail=False)
    def request(self, request, **kwargs):
        from rides.models import CustomUser
        from rides.serializers import TripSerializer

        available_drivers = CustomUser.objects.filter(
            is_driver=True, is_available=True
        ).annotate(trips=Count("trips_as_driver"))
        selected_driver = available_drivers.order_by("trips").first()
        trip = Trip.objects.create(
            passenger=selected_driver, driver=selected_driver, status="PENDING"
        )
        return response.Response(TripSerializer(trip).data, status=201)


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """

    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["GET"])
    def trending(self, request, **kwargs):
        # En DriverViewSet, crear endpoint que calcule average_score = Avg(Rating.score)
        # por conductor, ordene desc y devuelva los 5 primeros con average_score
        drivers = (
            User.objects.filter(is_driver=True)
            .annotate(average_score=Avg("trips_as_driver__rating__score"))
            .order_by("-average_score")[0:5]
        )

        serializer = UserSerializer(drivers, many=True)
        return response.Response(serializer.data)


class RatingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para listar, detallar y actualizar ratings, pero no borrar.
    """

    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
