def get_air_quality_status(ppm):
    """
    Menentukan status kualitas udara berdasarkan nilai ppm (MQ135).
    """
    if ppm is None:
        return "Tidak diketahui"
    
    try:
        ppm = float(ppm)
    except (ValueError, TypeError):
        return "Tidak valid"

    if ppm < 0:
        return "Tidak valid"
    elif ppm <= 100:
        return "Aman"                # Normal dan sehat
    elif ppm <= 120:
        return "Kurang Bersih"       # Mulai ada kontaminasi
    elif ppm <= 170:
        return "Tercemar"            # Udara mulai tidak sehat
    elif ppm <= 300:
        return "Polusi Berbahaya"    # Berbahaya untuk pernapasan
    elif ppm <= 999:
        return "Berbahaya Tinggi"    # Sangat berbahaya
    else:
        return "Diluar Batas"        # Di luar rentang pengukuran wajar
