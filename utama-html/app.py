import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)

DEFAULT_CONTROL = { "id": 1, "lamp": "OFF", "servo": "OFF", "soil_threshold": 2500, "auto_water_mode": "OFF", "lamp_auto": "OFF" }
DEFAULT_SENSORS = { "id": 1, "temperature": "0", "humidity": "0", "lux": "0", "soil": "0" }

def get_status_logic():
    sensor_data = DEFAULT_SENSORS
    control_data = DEFAULT_CONTROL
    try:
        # Ambil data sensor terakhir dari tabel 'latest_sensors', baris id=1
        sensor_response = supabase.table('latest_sensors').select("*").eq('id', 1).single().execute()
        if sensor_response.data:
            sensor_data = sensor_response.data
        
        # Ambil data kontrol dari tabel 'control_state', baris id=1
        control_response = supabase.table('control_state').select("*").eq('id', 1).single().execute()
        if control_response.data:
            control_data = control_response.data
    except Exception as e:
        print(f"Error saat mengambil data dari Supabase: {e}")

    # Logika untuk status terrarium (tetap sama)
    soil_value = int(sensor_data.get('soil', 0))
    soil_threshold = int(control_data.get('soil_threshold', 2500))
    if soil_value > soil_threshold:
        soil_status = "Low"
    else:
        soil_status = "Optimal"
    soil_moisture_percent = round(max(0, min(100, (4095 - soil_value) / 4095 * 100)), 1)
    
    humidity_value = float(sensor_data.get('humidity', 0))
    if humidity_value > 85: humidity_status = "High"
    elif humidity_value < 60: humidity_status = "Low"
    else: humidity_status = "Optimal"

    temp_value = float(sensor_data.get('temperature', 0))
    if temp_value > 30: temp_status = "High"
    elif temp_value < 20: temp_status = "Low"
    else: temp_status = "Optimal"
    
    lux_value = float(sensor_data.get('lux', 0))
    if lux_value > 1000: light_status = "High"
    elif lux_value < 100: light_status = "Low"
    else: light_status = "Optimal"
    
    all_statuses = [soil_status, humidity_status, temp_status, light_status]
    terrarium_condition = "Optimal"
    terrarium_message = "Terrarium Anda dalam kondisi baik."
    if "Low" in all_statuses or "High" in all_statuses:
        terrarium_condition = "Not Optimal"
        terrarium_message = "Periksa sensor yang statusnya Low/High."


    return {
        "sensor_data": sensor_data,
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
    return render_template('dashboard.html')

@app.route('/threshold')
def threshold():
    return render_template('threshold.html')
    
@app.route('/status')
def status():
    return jsonify(get_status_logic())

@app.route('/update_control', methods=['POST'])
def update_control():
    update_data = request.get_json()
    try:
        data, count = supabase.table('control_state').update(update_data).eq('id', 1).execute()
        return jsonify({"status": "success", "updated_data": data[1] if count[1] else None}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-control', methods=['GET'])
def get_control_data():
    try:
        response = supabase.table('control_state').select("*").eq('id', 1).single().execute()
        return jsonify(response.data or DEFAULT_CONTROL), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/data', methods=['POST'])
def receive_data():
    received_data = request.get_json()
    print(f"Menerima data dari ESP: {received_data}")
    try:
        data, count = supabase.table('latest_sensors').update(received_data).eq('id', 1).execute()
        return jsonify({"status": "success", "message": "Data berhasil diterima"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')