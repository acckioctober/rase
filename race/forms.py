from django import forms
from .models import Review, EventRegistration, Event, RaceType
from django.utils import timezone
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }


class EventRegistrationForm(forms.ModelForm):
    # Определение полей формы
    phone_number = PhoneNumberField(
        widget=forms.TextInput(),
        label='Номер телефона',
        required=True
    )

    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(start_datetime__gte=timezone.now()),
        label='Мероприятие'
    )

    race = forms.ModelChoiceField(
        queryset=RaceType.objects.none(),
        label='Участвующие группы'
    )

    class Meta:
        # Конфигурация модели и определение полей, которые должны быть в форме
        model = EventRegistration
        fields = ['phone_number', 'event', 'race', 'tshirt_size', 'city', 'club', 'payment_document']

    def __init__(self, *args, **kwargs):
        # Инициализация формы
        super().__init__(*args, **kwargs)
        self.initialize_field_classes()
        self.initialize_dynamic_fields()

    def initialize_field_classes(self):
        # Установка CSS классов для каждого поля формы
        for name, field in self.fields.items():
            css_class = 'form-control' if not isinstance(field.widget, forms.widgets.Select) else 'form-select'
            field.widget.attrs.update({'class': css_class})

    def initialize_dynamic_fields(self):
        # Инициализация динамических полей, в частности, настройка queryset для поля 'race'
        event_id = self.data.get('event') if 'event' in self.data else None
        if event_id:
            self.set_race_query_set(event_id)

    def set_race_query_set(self, event_id):
        # Установка queryset для поля 'race' на основе выбранного 'event'
        try:
            event = Event.objects.get(id=event_id, start_datetime__gte=timezone.now())
            self.fields['race'].queryset = event.race_types.all()
        except (ValueError, TypeError, Event.DoesNotExist):
            self.fields['race'].queryset = RaceType.objects.none()

    def clean(self):
        # Кастомная валидация формы
        cleaned_data = super().clean()
        self.validate_event_date(cleaned_data)
        self.check_duplicate_registration(cleaned_data)
        return cleaned_data

    def validate_event_date(self, cleaned_data):
        # Проверка даты мероприятия
        event = cleaned_data.get("event")
        if event and event.start_datetime < timezone.now():
            raise forms.ValidationError("Регистрация на выбранное мероприятие уже истекла.")

    def check_duplicate_registration(self, cleaned_data):
        # Проверка на дублирование регистрации
        user = self.initial.get("user")
        event = cleaned_data.get("event")
        race = cleaned_data.get("race")
        if EventRegistration.objects.filter(user=user, event=event, race=race).exists():
            raise forms.ValidationError("Вы уже зарегистрированы на это мероприятие в данной группе.")
