from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from .models import Event, Location, RaceType, Organizer, GalleryPhoto, Review, EventRegistration
from django.db.models import Prefetch
from .forms import ReviewForm, EventRegistrationForm
from django.core.paginator import Paginator
from django.http import JsonResponse


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")


class MainPageView(TemplateView):
    """
    The MainPageView class represents the view for the main page of the site. This view handles the display
    of upcoming and past events, as well as the latest reviews.
    """
    template_name = 'race/main_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_datetime = timezone.now()

        # Получение предстоящих и прошедших мероприятий
        context['upcoming_events'] = Event.objects.filter(
            start_datetime__gte=current_datetime).order_by('start_datetime')
        context['past_events'] = Event.objects.filter(
            start_datetime__lt=current_datetime).order_by('-start_datetime')

        # Получение последних 5 отзывов
        context['latest_reviews'] = Review.objects.order_by('-created_at')[:5]

        return context


class EventsView(ListView):
    """
    The EventsView class is responsible for displaying a list of events on the 'race/events.html' page.
    This class extends Django's ListView. It provides a list of events based on the filter
    selected by the user (all, upcoming, or past events). Pagination is implemented to limit
    the number of events displayed per page.
    """
    model = Event
    template_name = 'race/events.html'
    context_object_name = 'events'
    paginate_by = 6  # Количество событий на странице

    def get_queryset(self):
        current_datetime = timezone.now()
        filter_option = self.request.GET.get('filter', 'all')

        if filter_option == 'upcoming':
            return Event.objects.filter(start_datetime__gte=current_datetime).order_by('start_datetime')
        elif filter_option == 'past':
            return Event.objects.filter(start_datetime__lt=current_datetime).order_by('-start_datetime')
        else:
            return Event.objects.all().order_by('-start_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', 'all')
        return context


class PricingView(View):
    """
    The PricingView class extends Django's View class and is used to render the 'race/pricing.html' page.
    This view gathers data about upcoming events, including their associated race types and organizers,
    and passes this information to the template for rendering.
    """
    def get(self, request, *args, **kwargs):
        upcoming_events = Event.objects.filter(start_datetime__gte=timezone.now()).prefetch_related(
            'race_types', 'organizers'
        )
        return render(request, 'race/pricing.html', {'upcoming_events': upcoming_events})


class ContactView(TemplateView):
    template_name = 'race/contact.html'


class EventDetailView(DetailView):
    """
    The EventDetailView class provides a detailed view of an individual event.
    It extends Django's DetailView class to render a specific event's details.
    The view uses the 'race/detailed_event.html' template to display the information.
    """
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
        registrations = EventRegistration.objects.filter(event=event, is_active=True).select_related('user', 'race').order_by('race')

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