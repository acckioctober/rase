from django import forms
from .models import Review, EventRegistration, Event, RaceType
from django.utils import timezone

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }


class EventRegistrationForm(forms.ModelForm):
    """Event Registration Form with Dynamic Race Type Selection and Validation"""
    # Поле выбора мероприятия, отображает только предстоящие мероприятия
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(start_datetime__gte=timezone.now()),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Мероприятие'
    )

    # Поле выбора участвующих групп, изначально пустое
    race = forms.ModelChoiceField(
        queryset=RaceType.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Участвующие группы'
    )

    # Поле загрузки документа об оплате
    payment_document = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control-file'}),
        label='Документ об оплате'
    )

    # Поля даты рождения, города, клуба и размера футболки
    date_of_birth = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Дата рождения'
    )
    city = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Город'
    )
    club = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Клуб'
    )
    tshirt_size = forms.ChoiceField(
        choices=[('S', 'Small'), ('M', 'Medium'), ('L', 'Large')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Размер футболки'
    )

    class Meta:
        model = EventRegistration
        fields = ['event', 'race', 'date_of_birth', 'city', 'club', 'tshirt_size', 'payment_document']

    def __init__(self, *args, **kwargs):
        # Эта реализация учитывает:
        # Фильтрацию предстоящих событий при выборе мероприятия.
        # Обновление списка групп на основе выбранного мероприятия.
        # Проверку на то, что событие еще не наступило на момент отправки формы.
        # Проверку на повторную регистрацию пользователя на ту же группу в том же мероприятии.
        super().__init__(*args, **kwargs)
        if 'event' in self.data:
            try:
                event_id = int(self.data.get('event'))
                event = Event.objects.get(id=event_id, start_datetime__gte=timezone.now())
                self.fields['race'].queryset = event.race_types.all()
            except (ValueError, TypeError, Event.DoesNotExist):
                self.fields['race'].queryset = RaceType.objects.none()
        elif self.instance.pk:
            if self.instance.event.start_datetime >= timezone.now():
                self.fields['race'].queryset = self.instance.event.race_types.all()
            else:
                self.fields['race'].queryset = RaceType.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        event = cleaned_data.get("event")
        race = cleaned_data.get("race")
        user = self.initial.get("user")

        if event and event.start_datetime < timezone.now():
            raise forms.ValidationError("Регистрация на выбранное мероприятие уже истекла.")

        if EventRegistration.objects.filter(user=user, event=event, race=race).exists():
            raise forms.ValidationError("Вы уже зарегистрированы на это мероприятие в данной группе.")

        return cleaned_data
