from django.urls import path
from . import views

urlpatterns = [
    path('get-races-for-event/<int:event_id>/', views.get_races_for_event, name='get-races-for-event'),
    path('', views.main_page_view, name='main_page'),
    path('events/', views.events_view, name='events'),
    path('events/<int:pk>/add_review/', views.add_review, name='add_review'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),

    path('event-detail/<slug:event_slug>/', views.EventDetailView.as_view(), name='event_detail'),


    path('event-detail/<slug:event_slug>/registrations/', views.EventRegistrationsView.as_view(), name='event_registrations'),



    path('register-for-event/', views.EventRegistrationCreateView.as_view(), name='register_for_event'),
    path('race-registration-success/', views.RaceRegistrationSuccessView.as_view(), name='race_registration_success'),

]
