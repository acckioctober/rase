document.addEventListener('DOMContentLoaded', function() {
    const eventSelect = document.querySelector('select[name="event"]');
    const raceSelect = document.querySelector('select[name="race"]');

    eventSelect.addEventListener('change', function() {
        const eventId = this.value;
        fetch(`/get-races-for-event/${eventId}/`)
        .then(response => response.json())
        .then(data => {
            raceSelect.innerHTML = "<option value=''>Выберите группу</option>";
            data.races.forEach(race => {
                const option = document.createElement('option');
                option.value = race.id;
                option.textContent = race.name;
                raceSelect.appendChild(option);
            });
        });
    });
});

