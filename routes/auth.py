from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from werkzeug.security import check_password_hash, generate_password_hash
from firebase_admin import db
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__)
logging.basicConfig(level=logging.INFO)

def init_auth_routes(app, mysql):
    def is_mysql_online():
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"MySQL not available: {e}")
            return False

    def save_user_to_firebase(user):
        try:
            user_id = user.get('email').replace('.', '_')
            db.reference(f'users/{user_id}').set(user)
            logging.info(f"User saved to Firebase: {user['email']}")
        except Exception as e:
            logging.error(f"Error saving user to Firebase: {e}")

    def get_user_from_firebase(email):
        try:
            user_id = email.replace('.', '_')
            user = db.reference(f'users/{user_id}').get()
            if user:
                logging.info(f"User found in Firebase: {email}")
            return user
        except Exception as e:
            logging.error(f"Error fetching user from Firebase: {e}")
            return None

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            akun = None
            mysql_ok = is_mysql_online()

            if mysql_ok:
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute('SELECT username, password FROM tb_users WHERE email=%s', (email,))
                    akun = cursor.fetchone()
                except Exception as e:
                    logging.warning(f"MySQL login query failed: {e}")
                    mysql_ok = False

            if not akun:
                # Fallback ke Firebase
                firebase_user = get_user_from_firebase(email)
                if firebase_user and check_password_hash(firebase_user['password'], password):
                    session['loggedin'] = True
                    session['username'] = firebase_user['username']
                    return redirect(url_for('index'))
                else:
                    flash('Login gagal, email atau password salah', 'danger')
            else:
                if check_password_hash(akun[1], password):
                    session['loggedin'] = True
                    session['username'] = akun[0]
                    return redirect(url_for('index'))
                else:
                    flash('Login gagal, cek password anda', 'danger')

        return render_template('login.html')

    @auth_bp.route('/registrasi', methods=['GET', 'POST'])
    def registrasi():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            hashed_pw = generate_password_hash(password)

            mysql_ok = is_mysql_online()
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_pw,
                "created_at": datetime.now().isoformat()
            }

            already_exists = False
            if mysql_ok:
                try:
                    cursor = mysql.connection.cursor()
                    cursor.execute('SELECT * FROM tb_users WHERE username=%s OR email=%s', (username, email))
                    akun = cursor.fetchone()
                    if akun:
                        already_exists = True
                    else:
                        cursor.execute("INSERT INTO tb_users (username, email, password) VALUES (%s, %s, %s)",
                                       (username, email, hashed_pw))
                        mysql.connection.commit()
                        # Save to Firebase
                        save_user_to_firebase(user_data)
                        flash('Registrasi berhasil di MySQL dan Firebase! Silakan login.', 'success')
                except Exception as e:
                    logging.error(f"MySQL insert failed: {e}")
                    mysql_ok = False
                    flash('Gagal menyimpan ke MySQL, hanya Firebase yang berhasil.', 'warning')

            if not mysql_ok:
                # Check if user already exists in Firebase
                firebase_user = get_user_from_firebase(email)
                if firebase_user:
                    already_exists = True

            if already_exists:
                flash('Username atau email sudah digunakan', 'danger')
            else:
                # Save to Firebase if MySQL failed
                save_user_to_firebase(user_data)
                flash('Registrasi berhasil di Firebase! MySQL tidak tersedia, silakan login.', 'success')

            return redirect(url_for('auth.login'))

        return render_template('registrasi.html')

    @auth_bp.route('/logout')
    def logout():
        session.pop('loggedin', None)
        session.pop('username', None)
        return redirect(url_for('auth.login'))

    app.register_blueprint(auth_bp)
