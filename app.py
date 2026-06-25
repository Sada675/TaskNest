from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "frghyyty3445£$&&"

# ---------------- DATABASE CONNECTION ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sada123456@$",
    database="tasknest_db"
)
cursor = conn.cursor(dictionary=True)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email_prefix = request.form['email_prefix']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        email = email_prefix.strip() + "@gmail.com"
        hashed_password = generate_password_hash(password)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return render_template("register.html", error="Email already registered")

        # Insert user into DB
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()

        # **Login the user immediately**
        session['user_id'] = cursor.lastrowid  # id of the newly inserted user
        session['username'] = username

        # Redirect to dashboard
        return redirect('/dashboard')

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_prefix = request.form['email_prefix']
        password = request.form['password']
        email = email_prefix.strip() + "@gmail.com"

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        else:
            return render_template("login.html", error="Invalid Email or Password", show_forgot=True)

    return render_template("login.html", show_forgot=True)

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY id DESC", (session['user_id'],))
    tasks = cursor.fetchall()
    return render_template("dashboard.html", username=session['username'], tasks=tasks)

# ---------------- ADD TASK ----------------
@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date'] or None
        priority = request.form['priority']

        cursor.execute(
            "INSERT INTO tasks (user_id, title, description, due_date, priority, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], title, description, due_date, priority, 'pending')
        )
        conn.commit()
        return redirect('/dashboard')

    return render_template("add_task.html")

# ---------------- EDIT TASK ----------------
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM tasks WHERE id=%s AND user_id=%s", (task_id, session['user_id']))
    task = cursor.fetchone()
    if not task:
        return redirect('/dashboard')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date'] or None
        priority = request.form['priority']

        cursor.execute(
            "UPDATE tasks SET title=%s, description=%s, due_date=%s, priority=%s WHERE id=%s",
            (title, description, due_date, priority, task_id)
        )
        conn.commit()
        return redirect('/dashboard')

    return render_template("edit_task.html", task=task)

# ---------------- DELETE TASK ----------------
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect('/')

    cursor.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (task_id, session['user_id']))
    conn.commit()
    return redirect('/dashboard')

# ---------------- MARK TASK COMPLETED ----------------
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect('/')

    cursor.execute("UPDATE tasks SET status='completed' WHERE id=%s AND user_id=%s", (task_id, session['user_id']))
    conn.commit()
    return redirect('/dashboard')

# ---------------- FORGOT PASSWORD ----------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email_prefix = request.form['email_prefix']
        email = email_prefix.strip() + "@gmail.com"

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            session['reset_email'] = email
            return redirect('/reset-password')
        else:
            return render_template("forgot.html", error="Email not found!")

    return render_template("forgot.html")

# ---------------- RESET PASSWORD ----------------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_pass = request.form['new_password']
        confirm_pass = request.form['confirm_password']

        if new_pass != confirm_pass:
            return render_template("reset_password.html", error="Passwords do not match")

        hashed = generate_password_hash(new_pass)
        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, session['reset_email']))
        conn.commit()
        return redirect('/')

    return render_template("reset_password.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
