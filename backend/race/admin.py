import csv
from django.http import HttpResponse
from django.utils.encoding import smart_str

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


# class EventRegistrationAdmin(admin.ModelAdmin):
#     """
#     Class for displaying the EventRegistration model in the admin panel.
#     """
#     list_display = ['user', 'event', 'race', 'date_of_birth', 'city', 'club', 'tshirt_size',
#                     'payment_document_link', 'payment_confirmation', 'registered_at', 'is_active']
#
#     def payment_document_link(self, obj):
#         if obj.payment_document:
#             return format_html("<a href='{}'>Скачать</a>", obj.payment_document.url)
#         return "Нет документа"
#
#     payment_document_link.short_description = 'Документ об оплате'


class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'race', 'get_user_name', 'get_user_date_birth', 'phone_number', 'city',
                    'club', 'tshirt_size', 'payment_document_link',
                    'payment_confirmation', 'registered_at', 'is_active']

    list_filter = ['event', 'payment_confirmation', 'registered_at', 'is_active']

    actions = ['export_active_to_csv']

    def export_active_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="active_participants.csv"'
        response.write(u'\ufeff'.encode('utf8'))  # BOM для поддержки UTF-8 в Excel

        writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Заголовки столбцов
        writer.writerow([
            smart_str(u"Event"),
            smart_str(u"Race"),
            smart_str(u"User"),
            smart_str(u"Date of Birth"),
            smart_str(u"Phone Number"),
            smart_str(u"City"),
            smart_str(u"Club"),
            smart_str(u"T-Shirt Size"),
            smart_str(u"Registration Date"),
            smart_str(u"Is Active"),
        ])

        # Данные строк
        for registration in queryset.filter(is_active=True):
            full_name = registration.user.get_full_name() or registration.user.username
            date_of_birth = registration.user.date_birth.strftime(
                "%Y-%m-%d") if registration.user.date_birth else "Не указано"

            writer.writerow([
                smart_str(registration.event.title),
                smart_str(registration.race),
                smart_str(full_name),
                smart_str(date_of_birth),
                smart_str(registration.phone_number),
                smart_str(registration.city),
                smart_str(registration.club),
                smart_str(registration.tshirt_size),
                smart_str(registration.registered_at.strftime("%Y-%m-%d %H:%M")),
                smart_str(registration.is_active)
            ])

        return response

    export_active_to_csv.short_description = "Экспорт Активных участников в CSV"

    def payment_document_link(self, obj):
        if obj.payment_document:
            return format_html('<a href="{}" target="_blank">Посмотреть докумен</a>', obj.payment_document.url)
        return "Нет документа"

    payment_document_link.short_description = 'Документ об оплате'

    def get_user_name(self, obj):
        """
        Returns the user's last name and first name, if they are set,
         otherwise returns its login.
        """
        user = obj.user
        if user.first_name and user.last_name:
            return f"{user.last_name} {user.first_name}"
        else:
            return user.username

    get_user_name.short_description = 'Пользователь'

    def get_user_date_birth(self, obj):
        return obj.user.date_birth
    get_user_date_birth.short_description = 'Дата рождения'


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
