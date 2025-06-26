document.addEventListener('DOMContentLoaded', function() {

    function updateActiveButtons() {
        fetch('/status') // Menggunakan endpoint /status yang sudah ada
            .then(response => response.json())
            .then(data => {
                if (!data.control_data) return; // Keluar jika tidak ada data kontrol

                const controls = data.control_data;
                
                // Pengecekan untuk Soil Moisture Threshold
                const soilThreshold = controls.soil_threshold || 2500;
                let activeSoilBtnId = 'soil-medium-btn'; // Default
                if (soilThreshold === 2000) activeSoilBtnId = 'soil-low-btn';
                if (soilThreshold === 3000) activeSoilBtnId = 'soil-hard-btn';
                updateButtonGroup(['soil-low-btn', 'soil-medium-btn', 'soil-hard-btn'], activeSoilBtnId);

                // Pengecekan untuk Isopods Feeding Threshold
                const servoThreshold = controls.servo_threshold || 2;
                let activeServoBtnId = 'isopods-medium-btn'; // Default
                if (servoThreshold === 1) activeServoBtnId = 'isopods-low-btn';
                if (servoThreshold === 3) activeServoBtnId = 'isopods-hard-btn';
                updateButtonGroup(['isopods-low-btn', 'isopods-medium-btn', 'isopods-hard-btn'], activeServoBtnId);

                // Pengecekan untuk Light Density Threshold
                const lightThreshold = controls.light_threshold || 50;
                let activeLightBtnId = 'light-medium-btn'; // Default
                if (lightThreshold === 15) activeLightBtnId = 'light-low-btn';
                if (lightThreshold === 100) activeLightBtnId = 'light-hard-btn';
                updateButtonGroup(['light-low-btn', 'light-medium-btn', 'light-hard-btn'], activeLightBtnId);
                
                // Pengecekan untuk Humidity Threshold
                const humidityThreshold = controls.humidity_threshold || 75;
                let activeHumidityBtnId = 'humidity-medium-btn'; // Default
                if (humidityThreshold === 60) activeHumidityBtnId = 'humidity-low-btn';
                if (humidityThreshold === 85) activeHumidityBtnId = 'humidity-hard-btn';
                updateButtonGroup(['humidity-low-btn', 'humidity-medium-btn', 'humidity-hard-btn'], activeHumidityBtnId);

            })
            .catch(error => console.error('Gagal mengambil status untuk tombol aktif:', error));
    }

    /**
     * @param {string[]} buttonIds
     * @param {string} activeId
     */
    function updateButtonGroup(buttonIds, activeId) {
        buttonIds.forEach(id => {
            const button = document.getElementById(id);
            if (button) {
                if (id === activeId) {
                    button.classList.add('button-active');
                } else {
                    button.classList.remove('button-active');
                }
            }
        });
    }

    /**
      @param {object} command
     */
    function sendControlCommand(command) {
        fetch('/update_control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(command),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Perintah kontrol terkirim:', data);
            updateActiveButtons(); 
            alert('Pengaturan baru telah disimpan!');
        })
        .catch(error => console.error('Gagal mengirim perintah:', error));
    }

    // Soil Moisture
    document.getElementById('soil-low-btn')?.addEventListener('click', () => sendControlCommand({ soil_threshold: 3000 }));
    document.getElementById('soil-medium-btn')?.addEventListener('click', () => sendControlCommand({ soil_threshold: 2500 }));
    document.getElementById('soil-hard-btn')?.addEventListener('click', () => sendControlCommand({ soil_threshold: 1800 }));

    // Isopods Feeding
    document.getElementById('isopods-low-btn')?.addEventListener('click', () => sendControlCommand({ servo_threshold: 1 }));
    document.getElementById('isopods-medium-btn')?.addEventListener('click', () => sendControlCommand({ servo_threshold: 2 }));
    document.getElementById('isopods-hard-btn')?.addEventListener('click', () => sendControlCommand({ servo_threshold: 3 }));

    // Light Density
    document.getElementById('light-low-btn')?.addEventListener('click', () => sendControlCommand({ light_threshold: 15 }));
    document.getElementById('light-medium-btn')?.addEventListener('click', () => sendControlCommand({ light_threshold: 50 }));
    document.getElementById('light-hard-btn')?.addEventListener('click', () => sendControlCommand({ light_threshold: 100 }));

    // Humidity
    document.getElementById('humidity-low-btn')?.addEventListener('click', () => sendControlCommand({ humidity_threshold: 60 }));
    document.getElementById('humidity-medium-btn')?.addEventListener('click', () => sendControlCommand({ humidity_threshold: 75 }));
    document.getElementById('humidity-hard-btn')?.addEventListener('click', () => sendControlCommand({ humidity_threshold: 85 }));

    updateActiveButtons();
    setInterval(updateActiveButtons, 5000);

});