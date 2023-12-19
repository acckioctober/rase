from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from .models import Event, Location, RaceType, Organizer, GalleryImage, Review, EventRegistration
from django.db.models import Prefetch
from .forms import ReviewForm, EventRegistrationForm
from django.core.paginator import Paginator
from django.http import JsonResponse


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")

def main_page_view(request):
    current_date = timezone.now().date()
    # Получение предстоящих и прошедших мероприятий
    upcoming_events = Event.objects.filter(date__gte=current_date).order_by('-date')
    past_events = Event.objects.filter(date__lt=current_date).order_by('-date')

    # Получение последних 5 отзывов
    latest_reviews = Review.objects.order_by('-created_at')[:5]

    context = {
        'events': upcoming_events,
        'past_events': past_events,
        'latest_reviews': latest_reviews,
    }

    return render(request, 'race/main_page.html', context)


def add_review(request, pk):
    event = Event.objects.get(id=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.author = request.user
            review.save()
            return redirect('main_page')
    else:
        form = ReviewForm()

    return render(request, 'race/add_review.html', {'form': form, 'event': event})


def events_view(request):
    current_date = timezone.now().date()
    filter_option = request.GET.get('filter', 'all')

    if filter_option == 'upcoming':
        events = Event.objects.filter(date__gte=current_date).order_by('-date')
    elif filter_option == 'past':
        events = Event.objects.filter(date__lt=current_date).order_by('-date')
    else:
        events = Event.objects.all().order_by('-date')

    # Пагинация
    paginator = Paginator(events, 6)  # Показывать 9 мероприятий на странице
    page = request.GET.get('page')
    events = paginator.get_page(page)

    return render(request, 'race/events.html', {'events': events, 'paginator': paginator, 'page': page, 'filter': filter_option})


class PricingView(View):
    def get(self, request, *args, **kwargs):
        upcoming_events = Event.objects.filter(date__gte=timezone.now()).prefetch_related(
            'race_types', 'organizers'
        )
        return render(request, 'race/pricing.html', {'upcoming_events': upcoming_events})


class EventDetailView(DetailView):
    """A view for display details of a specific event"""
    model = Event
    template_name = 'race/detailed_event.html'
    context_object_name = 'event'
    slug_field = 'slug'
    slug_url_kwarg = 'event_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        # Преобразование широты и долготы
        if event.location.latitude and event.location.longitude:
            context['latitude'] = str(event.location.latitude).replace(',', '.')
            context['longitude'] = str(event.location.longitude).replace(',', '.')
        else:
            context['latitude'], context['longitude'] = None, None

        return context


class EventRegistrationsView(DetailView):
    """A view for display details of registrations."""
    model = Event
    template_name = 'race/event_registrations.html'
    context_object_name = 'event'
    slug_url_kwarg = 'event_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        registrations = EventRegistration.objects.filter(event=event).select_related('user', 'race').order_by('race')

        grouped_registrations = {}
        for registration in registrations:
            race_type = registration.race
            if race_type not in grouped_registrations:
                grouped_registrations[race_type] = []
            grouped_registrations[race_type].append(registration)
        context['grouped_registrations'] = grouped_registrations

        return context


def get_races_for_event(request, event_id):
    """A Django view function that retrieves and returns all race types
    associated with a specific event as JSON."""
    event = get_object_or_404(Event, id=event_id)
    races = event.race_types.all()
    data = {
        'races': [{'id': race.id, 'name': str(race)} for race in races]
    }
    return JsonResponse(data)


class EventRegistrationCreateView(LoginRequiredMixin, CreateView):
    """A view for creating new event registrations."""
    model = EventRegistration
    form_class = EventRegistrationForm
    template_name = 'race/register_for_event.html'
    success_url = reverse_lazy('race_registration_success')  # Redirect to a success page after successful registration
    login_url = 'users:login'  # Optional: specify the URL to redirect to for login, if not set, will use Django's default login URL

    def form_valid(self, form):
        form.instance.user = self.request.user  # Assign the current user to the registration
        response = super().form_valid(form)
        self.request.session['registration_successful'] = True  # Установка флага в сессии
        return response

    def get_form_kwargs(self):
        kwargs = super(EventRegistrationCreateView, self).get_form_kwargs()
        kwargs['initial']['user'] = self.request.user  # Adding the current user to the initial form data
        return kwargs


class RaceRegistrationSuccessView(TemplateView):
    """A view for displaying a success page after a user has successfully registered for a race."""
    template_name = 'race/race_registration_success.html'

    def dispatch(self, request, *args, **kwargs):
        # Check for the flag in the session
        if not request.session.get('registration_successful', False):
            return redirect('main_page')  # Redirect if the flag is not set
        # Remove the flag from the session
        request.session.pop('registration_successful', None)
        return super().dispatch(request, *args, **kwargs)
