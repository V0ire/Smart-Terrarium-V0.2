# app.py
from flask import Flask, render_template, request, jsonify, json

app = Flask(__name__)

DATA_FILE = 'data.json'
CONTROL_FILE = 'control.json'


def load_json_data(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Mengembalikan default jika file tidak ada atau rusak
        if 'control' in filepath:
            return {"lamp": "OFF", "servo": "OFF", "threshold": 2500}
        else:
            return {"temperature": 0, "humidity": 0, "lux": 0, "soil": 4095}

def save_json_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_status_logic():
    sensor_data = load_json_data(DATA_FILE)
    control_data = load_json_data(CONTROL_FILE)

    # Inisialisasi nilai default jika terjadi error konversi
    soil_value = 0
    humidity_value = 0.0
    temp_value = 0.0
    lux_value = 0.0
    
    try:
        # Mencoba mengubah data sensor, menggunakan nilai default jika gagal
        soil_value = int(sensor_data.get('soil', 0))
        humidity_value = float(sensor_data.get('humidity', 0))
        temp_value = float(sensor_data.get('temperature', 0))
        lux_value = float(sensor_data.get('lux', 0))
    except (ValueError, TypeError) as e:
        # Jika terjadi error saat konversi (misal: data tidak valid), cetak pesan error di terminal
        print(f"Peringatan: Tidak dapat memproses data sensor. Error: {e}")
        # Nilai akan tetap default (0), sehingga aplikasi tidak crash

    soil_threshold = int(control_data.get('threshold', 2500))

    # Logika untuk Soil Moisture
    if soil_value > soil_threshold + 500:
        soil_status = "Low"
    elif soil_value < soil_threshold - 500:
        soil_status = "High"
    else:
        soil_status = "Optimal"
    soil_moisture_percent = round(max(0, min(100, (4095 - soil_value) / 4095 * 100)), 1)

    # Logika untuk Humidity
    if humidity_value > 85:
        humidity_status = "High"
    elif humidity_value < 60:
        humidity_status = "Low"
    else:
        humidity_status = "Optimal"

    # Logika untuk Temperature
    if temp_value > 30:
        temp_status = "High"
    elif temp_value < 20:
        temp_status = "Low"
    else:
        temp_status = "Optimal"

    # Logika untuk Light Intensity
    if lux_value > 1000:
        light_status = "High"
    elif lux_value < 100:
        light_status = "Low"
    else:
        light_status = "Optimal"

    # Logika Kondisi Terrarium Keseluruhan
    all_statuses = [soil_status, humidity_status, temp_status, light_status]
    if "Low" in all_statuses or "High" in all_statuses:
        terrarium_condition = "Not Optimal"
        terrarium_message = "Periksa sensor yang statusnya Low/High."
    else:
        terrarium_condition = "Optimal"
        terrarium_message = "Terrarium Anda dalam kondisi baik."

    return {
        "sensor_data": {
            "temperature": temp_value,
            "humidity": humidity_value,
            "lux": lux_value,
            "soil": soil_value
        },
        "control_data": control_data,
        "soil_status": soil_status,
        "soil_moisture_percent": soil_moisture_percent,
        "humidity_status": humidity_status,
        "temp_status": temp_status,
        "light_status": light_status,
        "terrarium_condition": terrarium_condition,
        "terrarium_message": terrarium_message
    }


@app.route('/')
def home():
    context = get_status_logic()
    return render_template('dashboard.html', **context)

@app.route('/threshold')
def threshold():
    context = get_status_logic()
    return render_template('threshold.html', **context)

@app.route('/update_control', methods=['POST'])
def update_control():
    if request.is_json:
        update_data = request.get_json()
        
        # Memuat data kontrol saat ini
        control_data = load_json_data('control.json')
        
        # Memperbarui data dengan nilai baru
        control_data.update(update_data)
        
        # Menyimpan kembali ke file
        save_json_data('control.json', control_data)
        
        return jsonify({"status": "success", "updated_data": control_data}), 200
    
    return jsonify({"status": "error", "message": "Request must be JSON"}), 400
@app.route('/status')
def status():
    return jsonify(get_status_logic())
if __name__ == '__main__':
    # host='0.0.0.0' agar bisa diakses dari perangkat lain di jaringan yang sama
    app.run(debug=True, host='0.0.0.0')