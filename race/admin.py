from django.contrib import admin
from .models import (RaceType,
                     EventRegistration,
                     Location,
                     Event,
                     EventSchedule,
                     Organizer,
                     EventSummary,
                     GalleryPhoto,
                     Review)
from django.utils.html import format_html


class RaceTypeAdmin(admin.ModelAdmin):
    """Class for displaying the RaceType model in the admin panel"""
    list_display = ['distance', 'gender', 'min_age', 'registration_fee']
    list_filter = ['distance']
    search_fields = ['distance']


class EventRegistrationAdmin(admin.ModelAdmin):
    """Class for displaying the EventRegistration model in the admin panel"""
    list_display = ['user', 'event', 'race', 'date_of_birth', 'city', 'club', 'tshirt_size',
                    'payment_document_link', 'payment_confirmation', 'registered_at', 'is_active']

    def payment_document_link(self, obj):
        if obj.payment_document:
            return format_html("<a href='{}'>Скачать</a>", obj.payment_document.url)
        return "Нет документа"

    # Дополнительные методы, если необходимо отобразить связанные данные из модели пользователя
    def user_date_of_birth(self, obj):
        return obj.user.date_of_birth

    def user_city(self, obj):
        return obj.user.city

    def user_club(self, obj):
        return obj.user.club

    payment_document_link.short_description = 'Документ об оплате'
    user_date_of_birth.short_description = 'Дата рождения'
    user_city.short_description = 'Город'
    user_club.short_description = 'Клуб'


class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


# Регистрация моделей в админ-панели
admin.site.register(RaceType, RaceTypeAdmin)
admin.site.register(EventRegistration, EventRegistrationAdmin)
admin.site.register(Location)
admin.site.register(Event, EventAdmin)
admin.site.register(EventSchedule)
admin.site.register(Organizer)
admin.site.register(EventSummary)
admin.site.register(GalleryPhoto)
admin.site.register(Review)
