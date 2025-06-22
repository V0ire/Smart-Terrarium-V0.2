# app.py (Versi Supabase)
import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

# BARU: Inisialisasi koneksi ke Supabase menggunakan Environment Variables
# Pastikan Anda sudah mengatur ini di Vercel!
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__) # DIUBAH: Typo _name diperbaiki menjadi _name_

# DIHAPUS: Konstanta nama file tidak diperlukan lagi
# DATA_FILE = 'data.json'
# CONTROL_FILE = 'control.json'

# DIHAPUS: Fungsi untuk membaca/menulis file lokal tidak diperlukan lagi
# def load_json_data(filepath): ...
# def save_json_data(filepath, data): ...


@app.route('/get-control', methods=['GET'])
def get_control_data():
    """
    Endpoint ini membaca data kontrol dari tabel 'control_status' di Supabase
    dan mengirimkannya sebagai respons ke ESP.
    """
    try:
        # DIUBAH: Mengambil data dari Supabase, bukan file
        response = supabase.table('control_status').select("lamp, servo, threshold").eq('id', 1).single().execute()
        
        if response.data:
            return jsonify(response.data), 200
        else:
            # Jika data tidak ditemukan, kembalikan default
            return jsonify({"lamp": "OFF", "servo": "OFF", "threshold": 2500}), 404
            
    except Exception as e:
        print(f"Error saat mengambil data kontrol dari Supabase: {e}")
        return jsonify({"status": "error", "message": "Gagal membaca data kontrol"}), 500


@app.route('/data', methods=['POST'])
def receive_data():
    """
    Endpoint ini menerima data JSON dari ESP dan menyimpannya
    ke tabel 'sensor_data' di Supabase.
    """
    if request.is_json:
        received_data = request.get_json()
        print(f"Menerima data dari ESP: {received_data}")
        
        try:
            # DIUBAH: Menyimpan (update) data ke Supabase, bukan file
            supabase.table('sensor_data').update(received_data).eq('id', 1).execute()
            return jsonify({"status": "success", "message": "Data berhasil diterima"}), 200
        except Exception as e:
            print(f"Error saat menyimpan data sensor ke Supabase: {e}")
            return jsonify({"status": "error", "message": "Gagal menyimpan data sensor"}), 500
            
    return jsonify({"status": "error", "message": "Request harus dalam format JSON"}), 400


def get_status_logic():
    """
    Fungsi ini mengambil data sensor dan kontrol dari Supabase,
    memprosesnya, dan mengembalikan semua status.
    """
    try:
        # DIUBAH: Mengambil data sensor dan kontrol dari Supabase
        sensor_response = supabase.table('sensor_data').select("*").eq('id', 1).single().execute()
        control_response = supabase.table('control_status').select("*").eq('id', 1).single().execute()
        
        # Menggunakan data dari response, atau nilai default jika gagal
        sensor_data = sensor_response.data or {"temperature": 0, "humidity": 0, "lux": 0, "soil": 4095}
        control_data = control_response.data or {"lamp": "OFF", "servo": "OFF", "threshold": 2500}
    
    except Exception as e:
        print(f"Error saat mengambil data untuk logika status: {e}")
        sensor_data = {"temperature": 0, "humidity": 0, "lux": 0, "soil": 4095}
        control_data = {"lamp": "OFF", "servo": "OFF", "threshold": 2500}

    # Dari sini ke bawah, TIDAK ADA PERUBAHAN.
    # Semua logika tetap sama karena inputnya (sensor_data dan control_data)
    # adalah dictionary Python, sama seperti sebelumnya.

    soil_value = int(sensor_data.get('soil', 0))
    humidity_value = float(sensor_data.get('humidity', 0))
    temp_value = float(sensor_data.get('temperature', 0))
    lux_value = float(sensor_data.get('lux', 0))
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
        "sensor_data": {
            "temperature": temp_value, "humidity": humidity_value,
            "lux": lux_value, "soil": soil_value
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

# Rute-rute di bawah ini tidak perlu diubah karena mereka memanggil get_status_logic()
# yang sudah kita modifikasi untuk menggunakan Supabase.
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
            # DIUBAH: Langsung update data ke tabel 'control_status' di Supabase
            response = supabase.table('control_status').update(update_data).eq('id', 1).execute()
            return jsonify({"status": "success", "updated_data": response.data}), 200
        except Exception as e:
            print(f"Error saat update kontrol ke Supabase: {e}")
            return jsonify({"status": "error", "message": "Gagal update data kontrol"}), 500

    return jsonify({"status": "error", "message": "Request must be JSON"}), 400


@app.route('/status')
def status():
    return jsonify(get_status_logic())


if __name__ == '_main_':
    app.run(debug=True, host='0.0.0.0')