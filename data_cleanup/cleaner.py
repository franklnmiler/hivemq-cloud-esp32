from datetime import datetime, timedelta

def delete_30_oldest(mysql, firebase_ref, socketio, mysql_online_state):
    mysql_online, last_mysql_down = mysql_online_state

    deleted_mysql = 0
    if mysql_online:
        try:
            cursor = mysql.cursor()
            cursor.execute("""
                DELETE FROM tb_bme280
                ORDER BY waktu ASC
                LIMIT 30
            """)
            deleted_mysql = cursor.rowcount
            mysql.commit()
            cursor.close()
        except:
            mysql_online = False
            last_mysql_down = datetime.now()

    # Firebase deletion
    firebase_data = firebase_ref.get()
    deleted_firebase = 0
    if firebase_data:
        sorted_items = sorted(firebase_data.items(), key=lambda x: x[1].get('waktu', ''))
        for key, entry in sorted_items[:30]:
            try:
                firebase_ref.child(key).delete()
                deleted_firebase += 1
            except:
                continue

    print(f"[{datetime.now()}] Hapus 30 Data - MySQL: {deleted_mysql}, Firebase: {deleted_firebase}")
    socketio.emit('data_deleted', {
        'mysql': deleted_mysql,
        'firebase': deleted_firebase,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    return (mysql_online, last_mysql_down)
