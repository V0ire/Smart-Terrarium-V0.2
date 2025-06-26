document.addEventListener('DOMContentLoaded', function() {
    let currentControlState = {};

    // update dashboard
    function updateDashboard() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (!data.control_data || !data.sensor_data) return;

                currentControlState = data.control_data;

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

                updateButtonState('all-lamp-btn', currentControlState.lamp === 'ON');
                updateButtonState('lamp-auto-btn', currentControlState.lamp === 'AUTO');
                updateButtonState('auto-water-btn', currentControlState.auto_water_mode === 'ON');
            })
            .catch(error => console.error('Error fetching status:', error));
    }

    // button style
    function updateButtonState(buttonId, isActive) {
        const button = document.getElementById(buttonId);
        if (button) {
            if (isActive) {
                button.classList.add('button-active');
            } else {
                button.classList.remove('button-active');
            }
        }
    }

    // send control
    function sendControlCommand(command) {
        fetch('/update_control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(command),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Control Success:', data);
            updateDashboard();
        })
        .catch(error => console.error('Control Error:', error));
    }

    // button listeners
    document.getElementById('manual-water-btn')?.addEventListener('click', () => {
        console.log("Manual water activated, sending servo: ON");
        sendControlCommand({ pump_manual_trigger: 'ON' });
    });

    document.getElementById('feed-btn')?.addEventListener('click', () => {
        console.log("Feed button clicked, sending servo: ON");
        sendControlCommand({ servo: 'ON' });
    });

    document.getElementById('auto-water-btn')?.addEventListener('click', () => {
        const newState = currentControlState.auto_water_mode === 'AUTO' ? 'OFF' : 'AUTO';
        console.log(`Automatic water mode changed to: ${newState}`);
        sendControlCommand({ pump_mode: newState });
    });

    document.getElementById('lamp-auto-btn')?.addEventListener('click', () => {
        const newState = currentControlState.lamp === 'AUTO' ? 'OFF' : 'AUTO';
        console.log(`Lamp mode changed to: ${newState}`);
        sendControlCommand({ lamp: newState });
    });

    document.getElementById('all-lamp-btn')?.addEventListener('click', () => {
        const newState = currentControlState.lamp === 'ON' ? 'OFF' : 'ON';
        console.log(`Manual lamp state changed to: ${newState}`);
        sendControlCommand({ lamp: newState });
    });
    
    // initialization
    updateDashboard();
    setInterval(updateDashboard, 2000);
});