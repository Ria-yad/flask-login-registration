import MySQLdb
from MySQLdb import OperationalError
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'MySQL@123'
app.config['MYSQL_DB'] = 'flask_login_db'

mysql = MySQL(app)


def init_database():
    """Create database and users table if they do not exist."""
    connection = None
    cursor = None
    try:
        connection = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD']
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{app.config['MYSQL_DB']}`")
        cursor.execute(f"USE `{app.config['MYSQL_DB']}`")
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(120) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            )
            '''
        )
        connection.commit()
        print('Database ready.')
    except OperationalError as error:
        print(f'Database setup failed: {error}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:
            cur = mysql.connection.cursor()

            # Check if email already exists
            cur.execute('SELECT id FROM users WHERE email = %s', (email,))
            existing_user = cur.fetchone()

            if existing_user:
                flash('Email already registered. Please login.', 'error')
                cur.close()
                return redirect(url_for('register'))

            cur.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                (username, email, hashed_password)
            )
            mysql.connection.commit()
            cur.close()

            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except OperationalError as error:
            flash(f'Database error: {error}', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT id, username, password FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            cur.close()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful.', 'success')
                return redirect(url_for('index'))

            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
        except OperationalError as error:
            flash(f'Database error: {error}', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    print(f'Starting server at http://{host}:{port}')

    init_database()

    try:
        from waitress import serve
        print('Using Waitress WSGI server...')
        serve(app, host=host, port=port)
    except ImportError:
        print('Waitress not installed. Using Flask development server...')
        app.run(debug=True, use_reloader=False, host=host, port=port)
