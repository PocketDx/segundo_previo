from django.contrib import admin
from .models import CustomUser, Vehicle, Trip, Rating

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_driver', 'is_passenger', 'is_available')
    list_filter = ('is_driver', 'is_passenger', 'is_available')
    search_fields = ('username', 'email')
    ordering = ('id',)
    list_editable = ('is_driver', 'is_passenger', 'is_available')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'license_plate')

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'driver', 'requested_at', 'status')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'score', 'comment')
