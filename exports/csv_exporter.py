import csv
import os
from datetime import datetime

# Fungsi untuk ekspor data ke CSV
def export_to_csv(cursor, filename='sensor_data.csv'):
    # Mendapatkan data dari database
    cursor.execute("SELECT waktu, suhu, kelembapan, tekanan FROM tb_bme280 ORDER BY waktu DESC")
    rows = cursor.fetchall()

    # Menentukan path untuk menyimpan file CSV
    if not os.path.exists('exports'):
        os.makedirs('exports')

    # Membuka file CSV untuk ditulis
    filepath = os.path.join('exports', filename)
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Menulis header
        writer.writerow(['Waktu', 'Suhu (°C)', 'Kelembapan (%)', 'Tekanan (hPa)'])

        # Menulis data
        for row in rows:
            writer.writerow([row['waktu'].strftime('%Y-%m-%d %H:%M:%S'), row['suhu'], row['kelembapan'], row['tekanan']])

    return filepath
