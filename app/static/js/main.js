document.addEventListener('DOMContentLoaded', function () {
    const serviceModal = document.getElementById('service-modal');
    const serviceModalContent = document.getElementById('service-modal-content');
    const serviceModalClose = document.getElementById('service-modal-close');

    const standortModal = document.getElementById('standort-modal');
    const standortModalContent = document.getElementById('standort-modal-content');
    const standortModalClose = document.getElementById('standort-modal-close');

    const formularModal = document.getElementById('formular-modal');
    const formularModalContent = document.getElementById('formular-modal-content');
    const formularModalClose = document.getElementById('formular-modal-close');

    // Function to fetch and display service details
    document.querySelectorAll('.view-service').forEach(function(button) {
        button.addEventListener('click', function() {
            const serviceId = button.getAttribute('data-service-id');
            fetch(`/api/services/${serviceId}`)
                .then(response => response.text())
                .then(data => {
                    serviceModalContent.innerHTML = data;
                    serviceModal.classList.remove('hidden');
                })
                .catch(error => console.error('Error loading service details:', error));
        });
    });

    // Function to fetch and display standort details
    document.querySelectorAll('.view-standort').forEach(function(button) {
        button.addEventListener('click', function() {
            const standortId = button.getAttribute('data-standort-id');
            fetch(`/api/standorte/${standortId}`)
                .then(response => response.text())
                .then(data => {
                    standortModalContent.innerHTML = data;
                    standortModal.classList.remove('hidden');
                    setTimeout(() => initializeMap(standortId), 500);
                })
                .catch(error => console.error('Error loading standort details:', error));
        });
    });

    // Close modals
    serviceModalClose.addEventListener('click', function() {
        serviceModal.classList.add('hidden');
    });

    standortModalClose.addEventListener('click', function() {
        standortModal.classList.add('hidden');
    });

    formularModalClose.addEventListener('click', function() {
        formularModal.classList.add('hidden');
    });

    // Close modals on clicking outside the modal content
    document.addEventListener('click', function(event) {
        if (!serviceModalContent.contains(event.target) && !serviceModal.classList.contains('hidden')) {
            serviceModal.classList.add('hidden');
        }
        if (!standortModalContent.contains(event.target) && !standortModal.classList.contains('hidden')) {
            standortModal.classList.add('hidden');
        }
        if (!formularModalContent.contains(event.target) && !formularModal.classList.contains('hidden')) {
            formularModal.classList.add('hidden');
        }
    });

    // Initialize the map after modal is visible
    function initializeMap(standortId) {
        const mapElement = document.getElementById('map' + standortId);
        if (mapElement) {
            const address = mapElement.getAttribute('data-address');
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        const lat = data[0].lat;
                        const lon = data[0].lon;

                        const map = L.map(mapElement).setView([lat, lon], 15);
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }).addTo(map);
                        L.marker([lat, lon]).addTo(map)
                            .bindPopup('<b>' + mapElement.getAttribute('data-name') + '</b><br />' + address).openPopup();
                    } else {
                        mapElement.innerHTML = "Address not found!";
                    }
                })
                .catch(error => console.error('Error fetching the coordinates:', error));
        }
    }

    // Function to fetch and display formular details
    document.querySelectorAll('.view-formular').forEach(function(button) {
        button.addEventListener('click', function() {
            const formularId = button.getAttribute('data-formular-id');
            fetch(`/api/formulare/${formularId}`)
                .then(response => response.text())
                .then(data => {
                    const formularModalContent = document.getElementById('formular-modal-content');
                    formularModalContent.innerHTML = data;
                    const formularModal = document.getElementById('formular-modal');
                    formularModal.classList.remove('hidden');
    
                    // Attach event listener to the service link within the form modal
                    const serviceLink = formularModalContent.querySelector('.view-service');
                    if (serviceLink) {
                        serviceLink.addEventListener('click', function () {
                            const serviceId = serviceLink.getAttribute('data-service-id');
                            fetch(`/api/services/${serviceId}`)
                                .then(response => response.text())
                                .then(serviceData => {
                                    const serviceModalContent = document.getElementById('service-modal-content');
                                    serviceModalContent.innerHTML = serviceData;
                                    const serviceModal = document.getElementById('service-modal');
                                    serviceModal.classList.remove('hidden');
                                })
                                .catch(error => console.error('Error loading service details:', error));
                        });
                    }
                })
                .catch(error => console.error('Error loading formular details:', error));
        });
    });

    // Functionality to filter services based on search input and online availability
    const serviceSearchInput = document.getElementById('service-search');
    const onlineAvailableCheckbox = document.getElementById('online-available');

    serviceSearchInput.addEventListener('input', filterServices);
    onlineAvailableCheckbox.addEventListener('change', filterServices);

    function filterServices() {
        const searchValue = serviceSearchInput.value.toLowerCase();
        const isOnlineAvailable = onlineAvailableCheckbox.checked;

        document.querySelectorAll('#service-list > div').forEach(function(service) {
            const serviceName = service.querySelector('h2').textContent.toLowerCase();
            const canBeDoneOnline = service.querySelector('p').textContent.includes('Yes');

            if (
                serviceName.includes(searchValue) &&
                (!isOnlineAvailable || canBeDoneOnline)
            ) {
                service.classList.remove('hidden');
            } else {
                service.classList.add('hidden');
            }
        });
    }
});
