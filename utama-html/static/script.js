// static/script.js (Versi Baru yang Stateful)

document.addEventListener('DOMContentLoaded', function() {
    // Variabel untuk menyimpan status kontrol terakhir dari server
    // Ini akan menjadi "sumber kebenaran" kita
    let currentControlState = {};

    // --- FUNGSI UTAMA UNTUK UPDATE DASHBOARD ---
    function updateDashboard() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // Simpan status kontrol terbaru yang diterima dari server
                currentControlState = data.control_data;

                // Memperbarui teks dan data sensor (kode ini masih sama)
                document.getElementById('terrarium-condition').textContent = data.terrarium_condition;
                document.getElementById('terrarium-message').textContent = data.terrarium_message;
                document.getElementById('soil-moisture-percent').textContent = data.soil_moisture_percent + '%';
                document.getElementById('soil-status').textContent = data.soil_status;
                document.getElementById('humidity-value').textContent = data.sensor_data.humidity + '%';
                document.getElementById('humidity-status').textContent = data.humidity_status;
                document.getElementById('temp-value').textContent = data.sensor_data.temperature + '°C';
                document.getElementById('temp-status').textContent = data.temp_status;
                document.getElementById('light-value').textContent = data.sensor_data.lux + ' Lux';
                document.getElementById('light-status').textContent = data.light_status;

                // --- BAGIAN BARU: Memperbarui Tampilan Tombol Berdasarkan Status ---
                updateButtonState('all-lamp-btn', currentControlState.lamp);
                updateButtonState('manual-water-btn', currentControlState.servo);
                updateButtonState('feed-btn', currentControlState.servo);
                // Tambahkan tombol lain di sini jika perlu (misal: lamp1, lamp2)
            })
            .catch(error => console.error('Error fetching status:', error));
    }

    // --- FUNGSI BANTUAN UNTUK MENGUBAH STYLE TOMBOL ---
    function updateButtonState(buttonId, state) {
        const button = document.getElementById(buttonId);
        if (button) {
            if (state === 'ON') {
                button.classList.add('button-active'); // Tambah class .button-active jika ON
            } else {
                button.classList.remove('button-active'); // Hapus class .button-active jika OFF
            }
        }
    }

    // --- FUNGSI BANTUAN UNTUK MENGIRIM PERINTAH ---
    function sendControlCommand(command) {
        fetch('/update_control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(command),
        })
        .then(response => response.json())
        .then(data => console.log('Control Success:', data))
        .catch(error => console.error('Control Error:', error));
    }

    // --- BAGIAN BARU: EVENT LISTENER DENGAN LOGIKA TOGGLE ---

    // Tombol Lampu (All Lamp)
    document.getElementById('all-lamp-btn').addEventListener('click', () => {
        // Tentukan status baru: jika sekarang ON, maka jadi OFF, begitu juga sebaliknya
        const newLampState = currentControlState.lamp === 'ON' ? 'OFF' : 'ON';
        console.log(`Lamp state is ${currentControlState.lamp}, changing to ${newLampState}`);
        sendControlCommand({ lamp: newLampState });
    });

    // Tombol Manual Water
    document.getElementById('manual-water-btn').addEventListener('click', () => {
        const newServoState = currentControlState.servo === 'ON' ? 'OFF' : 'ON';
        console.log(`Servo state is ${currentControlState.servo}, changing to ${newServoState}`);
        sendControlCommand({ servo: newServoState });
    });

    // Tombol Feed Isopods (mengontrol servo yang sama)
    document.getElementById('feed-btn').addEventListener('click', () => {
        const newServoState = currentControlState.servo === 'ON' ? 'OFF' : 'ON';
        console.log(`Servo state is ${currentControlState.servo}, changing to ${newServoState}`);
        sendControlCommand({ servo: newServoState });
    });
    
    // Anda bisa menambahkan listener untuk tombol lain dengan logika toggle yang sama
    // Contoh:
    // document.getElementById('lamp1-btn').addEventListener('click', () => {
    //     const newLamp1State = currentControlState.lamp1 === 'ON' ? 'OFF' : 'ON';
    //     sendControlCommand({ lamp1: newLamp1State });
    // });


    // Jalankan update pertama kali saat halaman dimuat
    updateDashboard();
    // Atur update otomatis setiap 2 detik
    setInterval(updateDashboard, 2000);
});