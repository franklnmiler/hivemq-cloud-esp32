# config.py
import firebase_admin
from firebase_admin import credentials, db
import pymysql

# === Firebase Setup ===
def init_firebase():
    cred = credentials.Certificate("/home/irsyad/Unduhan/stasiun-cuaca-main2/stasiun-cuaca-firebase-b2220-firebase-adminsdk-fbsvc-f61dbcec82.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://stasiun-cuaca-firebase-b2220-default-rtdb.firebaseio.com/'
    })
    return db.reference("tb_bme280")

# === MySQL Setup for Galera ===
def init_mysql(app=None):
    MYSQL_CONFIG = {
        "host": "192.168.1.100",  # IP HAProxy atau node Galera
        "user": "irsyad",
        "password": "312310512",
        "database": "kelompok7",
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": 5,
        "read_timeout": 5,
        "write_timeout": 5,
        "autocommit": True
    }

    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        print("✅ Koneksi MySQL Galera berhasil")
        return connection
    except Exception as e:
        print(f"❌ Gagal koneksi ke MySQL Galera: {e}")
        raise e
