import os
from flask import Flask, render_template, request, jsonify, json
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)

def get_status_logic():
    try:
        sensor_response = supabase.table('latest_sensors').select("*").eq('id', 1).single().execute()
        sensor_data = sensor_response.data
        
        control_response = supabase.table('control_state').select("*").eq('id', 1).single().execute()
        control_data = control_response.data
    except Exception as e:
        print(f"Error saat mengambil data dari Supabase: {e}")
        sensor_data = {"temperature": 0, "humidity": 0, "lux": 0, "soil": 4095}
        control_data = {"lamp": "OFF", "servo": "OFF", "threshold": 2500}

    soil_value = 0
    humidity_value = 0.0
    temp_value = 0.0
    lux_value = 0.0
    
    try:
        soil_value = int(sensor_data.get('soil', 0))
        humidity_value = float(sensor_data.get('humidity', 0))
        temp_value = float(sensor_data.get('temperature', 0))
        lux_value = float(sensor_data.get('lux', 0))
    except (ValueError, TypeError) as e:
        print(f"Peringatan: Tidak dapat memproses data sensor. Error: {e}")

    soil_threshold = int(control_data.get('threshold', 2500))

    if soil_value > soil_threshold + 500:
        soil_status = "Low"
    elif soil_value < soil_threshold - 500:
        soil_status = "High"
    else:
        soil_status = "Optimal"
    soil_moisture_percent = round(max(0, min(100, (4095 - soil_value) / 4095 * 100)), 1)

    if humidity_value > 85:
        humidity_status = "High"
    elif humidity_value < 60:
        humidity_status = "Low"
    else:
        humidity_status = "Optimal"

    if temp_value > 30:
        temp_status = "High"
    elif temp_value < 20:
        temp_status = "Low"
    else:
        temp_status = "Optimal"

    if lux_value > 1000:
        light_status = "High"
    elif lux_value < 100:
        light_status = "Low"
    else:
        light_status = "Optimal"

    all_statuses = [soil_status, humidity_status, temp_status, light_status]
    if "Low" in all_statuses or "High" in all_statuses:
        terrarium_condition = "Not Optimal"
        terrarium_message = "Periksa sensor yang statusnya Low/High."
    else:
        terrarium_condition = "Optimal"
        terrarium_message = "Terrarium Anda dalam kondisi baik."

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
        try:
            data, count = supabase.table('control_state').update(update_data).eq('id', 1).execute()
            return jsonify({"status": "success", "updated_data": data[1] if count[1] else None}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Request must be JSON"}), 400

@app.route('/status')
def status():
    return jsonify(get_status_logic())

@app.route('/get-control', methods=['GET'])
def get_control_data():
    try:
        response = supabase.table('control_state').select("*").eq('id', 1).single().execute()
        return jsonify(response.data or {}), 200
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