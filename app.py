import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_socketio import SocketIO
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json
import logging
import pymysql
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db

# Modul eksternal
from routes.auth import init_auth_routes
from config import init_firebase, init_mysql
from data_cleanup.cleaner import delete_30_oldest
from exports.csv_exporter import export_to_csv
from utils import get_air_quality_status
from supabase import create_client, Client
import requests
from datetime import datetime
import os

SUPABASE_URL = "https://ukvshzaviipzmrqfevvo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVrdnNoemF2aWlwem1ycWZldnZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzODYwNzIsImV4cCI6MjA2MDk2MjA3Mn0.2ET83b9F46CkDaLcxWIoMamwTouNGwmXcrdJYndJvtI"  # pakai anon public key saja
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# Setup
app = Flask(__name__)
app.secret_key = 'your-secret-key'
CORS(app)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

firebase_ref = init_firebase()
mysql = init_mysql(app)
init_auth_routes(app, mysql)

logging.basicConfig(level=logging.INFO)

# Status DB
mysql_online = True
last_mysql_down = None

def is_mysql_alive():
    try:
        cursor = mysql.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return True
    except:
        return False

def should_use_firebase_only():
    global mysql_online, last_mysql_down
    return not mysql_online or (last_mysql_down and (datetime.now() - last_mysql_down).total_seconds() < 120)

def send_to_firebase(data, type='sensor'):
    """
    Mengirim data ke Firebase, dengan penambahan field 'type'.
    """
    if type == 'sensor':
        firebase_ref.child('sensor_data').push({**data, "waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    elif type == 'relay':
        firebase_ref.child('relay_data').push({**data, "waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

def send_data(data, type='sensor'):
    global mysql_online, last_mysql_down
    if should_use_firebase_only():
        send_to_firebase(data, type)
        return

    try:
        cursor = mysql.cursor()
        if type == 'sensor':
            sql = """
                INSERT INTO tb_bme280 (suhu, kelembapan, tekanan, altitude, status_udara, kebakaran, jarak_ultrasonik, waktu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data['suhu'], data['kelembapan'], data['tekanan'], data['altitude'],
                data['status_udara'], data['kebakaran'], data['jarak_ultrasonik'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            cursor.execute(sql, values)
        elif type == 'relay':
            sql = "INSERT INTO tb_relay_log (relay_index, state, waktu) VALUES (%s, %s, %s)"
            values = (data['relay_index'], data['state'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            cursor.execute(sql, values)

        mysql.commit()
        cursor.close()
        send_to_firebase(data, type)
    except Exception as e:
        print(f"❌ Gagal simpan ke MySQL ({type}), fallback Firebase: {e}")
        mysql_online = False
        last_mysql_down = datetime.now()
        send_to_firebase(data, type)



        

def mysql_health_check():
    global mysql_online, last_mysql_down
    if last_mysql_down and (datetime.now() - last_mysql_down).total_seconds() < 120:
        return
    try:
        if is_mysql_alive():
            mysql_online = True
            last_mysql_down = None
            print("✅ MySQL kembali online.")
        else:
            raise Exception("Timeout")
    except:
        mysql_online = False
        last_mysql_down = datetime.now()
        print("❌ MySQL masih mati.")

# === MQTT Handler ===
def on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))

        if msg.topic == 'iot/esp32/data':
            suhu = payload.get('suhu')
            kelembapan = payload.get('kelembapan')
            tekanan = payload.get('tekanan')
            altitude = payload.get('altitude')
            mq135_ppm = payload.get('mq135_ppm')
            jarak = payload.get('jarak_ultrasonik')
            kebakaran = payload.get('kebakaran')
            lokasi = payload.get('lokasi')
            latitude = payload.get('latitude')
            longitude = payload.get('longitude')

            if None in [suhu, kelembapan, tekanan, altitude, mq135_ppm, jarak]:
                return

            status_udara = get_air_quality_status(mq135_ppm)
            sensor_data = {
                "suhu": suhu, "kelembapan": kelembapan, "tekanan": tekanan,
                "altitude": altitude, "mq135_ppm": mq135_ppm, "jarak_ultrasonik": jarak,
                "status_udara": status_udara, "kebakaran": kebakaran,
                "lokasi": lokasi, "latitude": latitude, "longitude": longitude
            }

            send_data(sensor_data, 'sensor')
            socketio.emit('new_data', {**sensor_data, "waktu": datetime.now().strftime('%H:%M:%S')})
            print("📥 Data sensor berhasil diproses")

        elif msg.topic == 'iot/esp8266/relay':
            relay_index = payload.get('relay')
            state = payload.get('state')
            if relay_index is not None and state is not None:
                relay_data = {
                    "relay_index": relay_index,
                    "state": state
                }
                send_data(relay_data, 'relay') # Send to database
                socketio.emit('relay_update', {'relay_index': relay_index, 'state': state}) # Send to SocketIO

                cursor = mysql.cursor()
                cursor.execute("INSERT INTO tb_relay_log (relay_index, state, waktu) VALUES (%s, %s, %s)", (relay_index, state, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

                # Update tb_relay
                cursor.execute("SELECT id FROM tb_relay WHERE relay_channel = %s", (relay_index,))
                if cursor.fetchone():
                    cursor.execute("UPDATE tb_relay SET status=%s, waktu=NOW() WHERE relay_channel=%s", (state, relay_index))
                else:
                    cursor.execute("INSERT INTO tb_relay (relay_channel, status, waktu) VALUES (%s, %s, NOW())", (relay_index, state))

                mysql.commit()
                cursor.close()
                print("📥 Data relay disimpan ke log & status")

    except Exception as e:
        logging.error(f"❌ Gagal proses MQTT: {e}")

def start_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set("irsyad26", "Irsyad261203")
    mqtt_client.tls_set()
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect("7bf8eb8dc92a4636b2ec3632ce6b177a.s1.eu.hivemq.cloud", 8883, 60)
    mqtt_client.subscribe("iot/esp32/data")
    mqtt_client.subscribe("iot/esp8266/relay")
    mqtt_client.loop_start()
    print("✅ MQTT listener aktif")

# === ROUTES ===
@app.route('/')
def index():
    if 'loggedin' in session:
        latest_data = []
        if should_use_firebase_only():
            data = firebase_ref.child('sensor_data').get() # Changed to only get sensor data
            if data:
                # Filter out only sensor data ('type' : 'sensor_data')
                latest_data = [v for v in data.values() if v.get('type') == 'sensor_data']
                latest_data = sorted(latest_data, key=lambda x: x.get('waktu', ''), reverse=True)[:10]
        else:
            try:
                cursor = mysql.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT * FROM tb_bme280 ORDER BY waktu DESC LIMIT 10")
                latest_data = cursor.fetchall()
                cursor.close()
            except:
                mysql_online = False
                last_mysql_down = datetime.now()
        return render_template('index.html', data=latest_data)
    flash("Silakan login terlebih dahulu", "danger")
    return redirect(url_for('auth.login'))


@app.route('/esp32/cam')
def esp32_cam():
    if 'loggedin' not in session:
        flash("Silakan login terlebih dahulu", "danger")
        return redirect(url_for('auth.login'))
    return render_template('esp32_cam.html')
def save_esp32_photo():
    try:
        # Ambil gambar dari ESP32-CAM
        image_url = "http://192.168.1.200/capture"
        response = requests.get(image_url, timeout=40)

        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, Gagal ambil gambar dari ESP32")

        # Nama file: timestamped
        filename = f"esp32_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Upload gambar ke Supabase Storage
        result = supabase.storage.from_('datacctv').upload(
            path=filename,
            file=response.content,
            file_options={"content-type": "image/jpeg"}
        )

        # Dapatkan URL publik untuk gambar
        public_url = supabase.storage.from_('datacctv').get_public_url(filename)
        print(f"✅ Gambar disimpan di: {public_url}")

        return {
            "message": "Gambar berhasil disimpan",
            "filename": filename,
            "url": public_url
        }
    except Exception as e:
        print(f"❌ Gagal ambil gambar atau simpan ke Supabase: {str(e)}")
        return {"error": str(e)}, 500

    



@app.route('/control/relay')
def relay_control():
    return render_template('relay_control.html')

@app.route('/relay/log')
def relay_log():
    try:
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM tb_relay_log ORDER BY waktu DESC LIMIT 50")
        logs = cursor.fetchall()
        cursor.close()
        return render_template('relay_log.html', logs=logs)
    except Exception as e:
        logging.error(f"❌ Gagal ambil log relay: {e}")
        return "Error"

@app.route('/api/relay-control', methods=['POST'])
def relay_control_api():
    data = request.get_json()
    relay_index = data.get('relay')
    state = data.get('state')  # "ON" / "OFF"

    if relay_index is None or state is None:
        return jsonify({'error': 'Data tidak lengkap'}), 400

    try:
        cursor = mysql.cursor()
        cursor.execute("INSERT INTO tb_relay_log (relay_index, state, waktu) VALUES (%s, %s, %s)", (relay_index, state, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        cursor.execute("SELECT id FROM tb_relay WHERE relay_channel = %s", (relay_index,))
        if cursor.fetchone():
            cursor.execute("UPDATE tb_relay SET status=%s, waktu=NOW() WHERE relay_channel=%s", (state, relay_index))
        else:
            cursor.execute("INSERT INTO tb_relay (relay_channel, status, waktu) VALUES (%s, %s, NOW())", (relay_index, state))

        mysql.commit()
        cursor.close()
        return jsonify({'message': 'Relay status & log disimpan'})
    except Exception as e:
        logging.error(f"❌ Gagal simpan relay ke DB: {e}")
        return jsonify({'error': 'DB error'}), 500
    


@app.route('/api/relay/status', methods=['GET'])
def get_relay_status():
    try:
        cursor = mysql.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT relay_channel, status, waktu
            FROM tb_relay
            ORDER BY relay_channel
        """
        cursor.execute(query)
        relays = cursor.fetchall()
        cursor.close()
        return jsonify({"relays": relays})
    except Exception as e:
        logging.error(f"❌ Gagal ambil status relay: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/bme280/export-csv')
def export_csv():
    try:
        cursor = mysql.cursor(pymysql.cursors.DictCursor)
        filepath = export_to_csv(cursor)
        cursor.close()
        return send_file(filepath, as_attachment=True, download_name='sensor_data.csv', mimetype='text/csv')
    except Exception as e:
        logging.error(f"❌ CSV export error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bme280/chart-multi')
def get_chart_data():
    try:
        cursor = mysql.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT waktu, suhu, kelembapan, tekanan FROM tb_bme280 ORDER BY waktu DESC LIMIT 20")
        rows = cursor.fetchall()
        cursor.close()

        rows = sorted(rows, key=lambda x: x['waktu'])
        labels = [row['waktu'].strftime('%H:%M:%S') for row in rows]
        suhu = [row['suhu'] for row in rows]
        kelembapan = [row['kelembapan'] for row in rows]
        tekanan = [row['tekanan'] for row in rows]

        return jsonify({'labels': labels, 'suhu': suhu, 'kelembapan': kelembapan, 'tekanan': tekanan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('[WebSocket] Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('[WebSocket] Client disconnected')

# === Scheduler Jobs ===
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: delete_30_oldest(mysql, firebase_ref, socketio, (mysql_online, last_mysql_down)), 'interval', minutes=80)
scheduler.add_job(mysql_health_check, 'interval', minutes=2)
scheduler.start()

# === RUN ===
if __name__ == '__main__':
    start_mqtt()
    print("🚀 App berjalan di http://192.168.1.100:5002")
    socketio.run(app, host='192.168.1.100', port=5002, debug=True)

