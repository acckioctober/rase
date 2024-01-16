"""
Database models.
"""
from django.urls import reverse
from django.utils import timezone
from django.db import models
import uuid
import os

import requests
from urllib.parse import urlencode


import logging

from django.utils.text import slugify

from race_project import settings
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)


def payment_docs_file_path(instance, filename):
    """Generate file path for new payment document."""
    event_slug = str(instance.event.slug).replace('-', '_')
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'payment_docs', event_slug, filename)


def event_image_file_path(instance, filename):
    """Generate file path for event image using the event slug and original filename."""
    event_slug = str(instance.slug).replace('-', '_')
    return os.path.join('events', 'image', event_slug, filename)


def event_protocol_file_path(instance, filename):
    """Generate file path for event protocol using the event slug and original filename."""
    event_slug = str(instance.event.slug).replace('-', '_')
    return os.path.join('events', 'protocol', event_slug, filename)


def event_photos_file_path(instance, filename):
    """Generate file path for event photos using the event slug and original filename."""
    event_slug = str(instance.event.slug).replace('-', '_')
    return os.path.join('events', 'photos', event_slug, filename)


class RaceType(models.Model):
    """Model representing a race type or category."""
    DISTANCE_CHOICES = [
        (5, '5 км'),
        (10, '10 км'),
        (15, '15 км'),
        (20, '20 км'),
    ]
    GENDER_CHOICES = [
        ('M', 'Муж.'),
        ('F', 'Жен.'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    min_age = models.PositiveSmallIntegerField(verbose_name="Минимальный возраст")
    distance = models.PositiveSmallIntegerField(choices=DISTANCE_CHOICES, verbose_name="Дистанция")
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость регистрации")

    def __str__(self):
        return f"{self.distance} км {self.get_gender_display()} {self.min_age} лет и старше (взнос {self.registration_fee} руб.)"

    class Meta:
        verbose_name = "Тип забега"
        verbose_name_plural = "Типы забегов"


class Location(models.Model):
    """Model representing a location address of sports event."""
    street = models.CharField(max_length=256, verbose_name="Улица")
    house_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер дома")
    city = models.CharField(max_length=256, verbose_name="Город")
    postal_code = models.CharField(max_length=6, verbose_name="Почтовый индекс")
    country = models.CharField(max_length=100, verbose_name="Страна")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота")

    def __str__(self):
        return f"{self.street}, {self.house_number}, {self.city}, {self.postal_code}, {self.country}"

    def save(self, *args, **kwargs):
        """Save method for getting the coordinates if they are not already set."""
        if not (self.latitude and self.longitude):
            self.latitude, self.longitude = self.geocode_address()
        super().save(*args, **kwargs)

    def geocode_address(self):
        """Method for geocoding the location address using Nominatim from OpenStreetMap."""
        params = {
            'format': 'json',
            'street': f"{self.street} {self.house_number}",
            'city': self.city,
            'postalcode': self.postal_code,
            'country': self.country,
        }
        url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            if results:
                return float(results[0]['lat']), float(results[0]['lon'])
        return None, None

    class Meta:
        verbose_name = "Место проведения"
        verbose_name_plural = "Места проведения"


class Event(models.Model):
    """Model representing a sports event."""
    EVENT_TYPES = [
        ("trail", "Трейл"),
        ("cross", "Кросс"),
        ("mountain", "Горный"),
        ("road", "Дорожный"),
        # Добавьте другие типы событий при необходимости
    ]
    title = models.CharField(max_length=255, verbose_name="Название мероприятия")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL-имя для мероприятия")
    description = models.TextField(verbose_name="Описание мероприятия")
    event_rules = models.TextField(verbose_name="Условия участия")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, verbose_name="Тип мероприятия")
    start_datetime = models.DateTimeField(verbose_name="Начало мероприятия", db_index=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Место проведения мероприятия")
    total_slots = models.PositiveIntegerField(verbose_name="Всего мест")
    is_upcoming = models.BooleanField(default=True, verbose_name="Предстоящее мероприятие")
    image = models.ImageField(upload_to=event_image_file_path, verbose_name="Изображение для мероприятия")
    race_types = models.ManyToManyField(RaceType, verbose_name="Участвующие группы")

    def get_absolute_url(self):
        """Getting the absolute event URL."""
        return reverse('event_detail', kwargs={'event_slug': self.slug})

    def get_registrations_url(self):
        """Получение абсолютного URL для страницы регистраций мероприятия."""
        return reverse('event_registrations', kwargs={'event_slug': self.slug})

    def days_left(self):
        """Return days left for the event."""
        delta = self.start_datetime.date() - timezone.now().date()
        return delta.days

    def get_free_slots(self):
        """Returns quantity of free slots or the event."""
        registrations_count = EventRegistration.objects.filter(event=self, is_active=True).count()
        return self.total_slots - registrations_count

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"


# class EventRegistration(models.Model):
#     """Model representing a user's registration for a race."""
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
#                              verbose_name="Пользователь", related_name="registrations")
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие")
#     race = models.ForeignKey(RaceType, on_delete=models.CASCADE, verbose_name="Участвующие группы")
#     payment_document = models.FileField(upload_to=payment_docs_file_path, verbose_name="Документ об оплате")
#     date_of_birth = models.DateField(verbose_name="Дата рождения")
#     city = models.CharField(max_length=255, verbose_name="Город")
#     club = models.CharField(max_length=255, blank=True, null=True, verbose_name="Клуб")
#     tshirt_size = models.CharField(max_length=3, choices=[('S', 'Small'), ('M', 'Medium'), ('L', 'Large')], verbose_name="Размер футболки")
#     payment_confirmation = models.BooleanField(default=False, verbose_name="Подтверждение оплаты")
#     registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
#     is_active = models.BooleanField(default=True, verbose_name="Активная регистрация")
#
#     def __str__(self):
#         return f"Регистрация {self.user} на {self.race} в мероприятии {self.event}"
#
#     class Meta:
#         verbose_name = "Регистрация на забег"
#         verbose_name_plural = "Регистрации на забеги"


class EventRegistration(models.Model):
    """Model representing a user's registration for a race."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name="Пользователь", related_name="registrations")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие")
    race = models.ForeignKey(RaceType, on_delete=models.CASCADE, verbose_name="Участвующие группы")
    payment_document = models.FileField(upload_to=payment_docs_file_path, verbose_name="Документ об оплате")
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name="Номер телефона")
    city = models.CharField(max_length=255, verbose_name="Город")
    club = models.CharField(max_length=255, blank=True, null=True, verbose_name="Клуб")
    tshirt_size = models.CharField(max_length=3, choices=[('S', 'Small'), ('M', 'Medium'), ('L', 'Large')], verbose_name="Размер футболки")
    payment_confirmation = models.BooleanField(default=False, verbose_name="Подтверждение оплаты")
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    is_active = models.BooleanField(default=True, verbose_name="Активная регистрация")

    def __str__(self):
        return f"Регистрация {self.user} на {self.race} в мероприятии {self.event}"

    class Meta:
        verbose_name = "Регистрация на забег"
        verbose_name_plural = "Регистрации на забеги"




class EventSchedule(models.Model):
    """Model representing the schedule of a sports event."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="schedules", verbose_name="Мероприятие")
    start_time = models.TimeField(verbose_name="Время начала")
    description = models.CharField(max_length=255, verbose_name="Описание")

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.description}"

    class Meta:
        verbose_name = "Программа мероприятия"
        verbose_name_plural = "Программа мероприятий"


class Organizer(models.Model):
    """Model representing an organizer of a sports event."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Организатор")
    contact = models.CharField(max_length=255, blank=True, verbose_name="Контактные данные")
    payment_details = models.TextField(blank=True, verbose_name="Реквизиты для оплаты")
    event = models.ManyToManyField(Event, related_name="organizers", verbose_name="Событие")

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "Организатор"
        verbose_name_plural = "Организаторы"


class EventSummary(models.Model):
    """
    The EventSummary class represents a summary and protocol for a specific event.
    """
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='summary', verbose_name="Мероприятие")
    text = models.TextField(blank=True, null=True, verbose_name="Резюме мероприятия")
    file = models.FileField(upload_to=event_protocol_file_path, verbose_name="Протокол мероприятия")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    def __str__(self):
        return f"Резюме для мероприятия {self.event.title}"

    class Meta:
        verbose_name = 'Резюме для мероприятия'
        verbose_name_plural = 'Резюме для мероприятий'


class GalleryPhoto(models.Model):
    """
    The GalleryPhoto class links photos to specific events, featuring optional titles, photo uploads,
    and auto-recorded upload timestamps.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos', verbose_name="Мероприятие")
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Заголовок')
    photo = models.ImageField(upload_to=event_photos_file_path, verbose_name='Фотография')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    def __str__(self):
        return f"Изображение для галереи {self.event.title}"

    class Meta:
        verbose_name = 'Изображение для галереи'
        verbose_name_plural = 'Изображения для галереи'


class Review(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews', verbose_name="Мероприятие")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Отзыв на {self.event.title} от {self.author.get_username()}"
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
