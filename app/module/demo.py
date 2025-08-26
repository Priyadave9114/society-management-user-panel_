from app import app,cursor,mydb
import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, flash, session,url_for

@app.route('/index')
def index():
    return render_template('index.html')

# Registration Page
@app.route('/registration',methods=["GET","POST"])
def registration():
    if request.method == 'POST':
        # this is userid validation
        userid = request.form['userid']
        pattern = r'^[A-Za-z0-9]{8,10}$'
        if not re.match(pattern, userid):
            flash("User ID must be 8-10 characters long with A-Z, a-z, 0-9 only.")
            return redirect('/registration')

        # 2. Check uniqueness from DB
        cursor.execute("SELECT * FROM users WHERE userid = %s", (userid,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("User ID already exists. Try a different one.")
            return redirect('/registration')

        # this is password validation
        password = request.form['password']
        pwd_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*()]).{6,}$'
        if not re.match(pwd_pattern, password):
            flash("Password must contain A-Z, a-z, 0-9, and !@#$%^&*()")
            return redirect(url_for('registration'))

        # this is reenter password
        repassword = request.form['repassword']

        # this is email validation
        email = request.form['email']
        if not (email.endswith("@gmail.com") or email.endswith("@yahoo.com")):
            flash("Only Gmail and Yahoo email addresses are allowed.")
            return redirect(url_for('registration'))

        # this is mobile number validation
        country_code = request.form['country_code']
        mobile = request.form['mobile']
        if not re.match(r'^[0-9]{10}$', mobile):
            flash("Mobile number must be exactly 10 digits.")
        full_mobile = country_code + mobile

        wing = request.form['wing']
        flat_number = request.form['flat_number']


        security_question = request.form['security_question']
        security_answer = request.form['security_answer']

        if password != repassword:
            flash("Password do not match.")
            return redirect(url_for('registration'))
        try:
                cursor.execute("""
                    INSERT INTO users (userid, password,repassword, email, mobile, security_question, security_answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (userid, password,repassword, email, mobile, security_question, security_answer))
                mydb.commit()
                flash("Registration successful")
                return redirect(url_for('login'))
        except Exception as e:
                print("Database Error:", e)
                flash(f"Error: {str(e)}", "danger")
                return redirect(url_for('login'))
    return render_template('registration.html')

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    # Initialize attempts if not already in session
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == 'POST':
        # Block if attempts reached 3
        if session['login_attempts'] >= 3:
            flash("Too many failed login attempts. Please try again later.")
            return redirect(url_for('forgot'))

        userid = request.form["userid"]
        password = request.form["password"]

        cursor.execute("SELECT userid, email FROM users WHERE userid=%s AND password=%s", (userid, password))
        user = cursor.fetchone()

        if user:
            session['userid'] = user[0]   
            session['email'] = user[1]    
            flash("Login successful", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "not-success")
            return redirect(url_for('login'))
    return render_template('login.html')

   
   
    # if request.method == 'POST':
    #     userid = request.form["userid"]
    #     password = request.form["password"]

    #     cursor.execute("SELECT userid, email FROM users WHERE userid=%s AND password=%s", (userid, password))
    #     user = cursor.fetchone()

    #     if user:
    #         flash("Login successful", "success")
    #         return redirect(url_for('index'))
    #     else:
    #         flash("Invalid credentials", "danger")
    #         return redirect(url_for('login'))

    # return render_template('login.html')
# Forgot Password Page
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        userid = request.form['userid']
        return redirect(url_for('reset'))
    return render_template('forgot.html')


@app.route('/reset')
def reset():
    return render_template('reset.html')

# maintenance 
base_amount = 2000
penalty = 0.10
due_date = datetime(2025, 7, 1)  
def calculate_amount():
    today = datetime.today()
    months_late = (today.year - due_date.year) * 12 + (today.month - due_date.month)

    if months_late == 0:  # Same month
        if 1 <= today.day <= 10:
            return base_amount
        else:
            return base_amount * 1.10  # 10% penalty
    else:
        return base_amount * (1.10 ** months_late)


@app.route("/maintenance", methods=["GET", "POST"])
def maintenance():
    if request.method == "POST":
        userid = request.form["userid"]
        email = request.form["email"]
        amount = request.form["amount"]
        # base_amount = request.form["base_amount"]
        # penalty = request.form["penalty"]

        # Send data to payment.html
        return render_template("payment.html", userid=userid, email=email, amount=amount)

    userid = session.get("userid", "Unknown")
    email = session.get("email", "unknown@example.com")
    amount = 2000  # Default maintenance amount
    return render_template("maintenance.html", userid=userid, email=email, amount=amount)

@app.route("/process_payment", methods=["POST"])
def process_payment():
    userid = request.form.get("userid")
    email = request.form.get("email")
    amount = request.form.get("amount")
    payment_method = request.form.get("payment_method")

    if not userid or not email:
        return "Missing user details. Please go back and try again.", 400

    if payment_method == "cash":
        message = "You need to go to the society office and pay in cash."
        return render_template("payment_success.html", userid=userid, email=email, amount=amount, message=message)

    message = f"Redirecting to {payment_method.upper()} payment gateway..."
    return render_template("payment_success.html", userid=userid, email=email, amount=amount, message=message)


@app.route("/success", methods=["POST"])
def success():
    return "<h2> Payment Successful!</h2><p>Thank you for your payment.</p>"


# complaint
@app.route("/complaint", methods=["GET", "POST"])
def complaint():
     if request.method == "POST":
        userid = session["userid"]   # take userid from session
        complaint_type = request.form.get("complaint_type")
        details = request.form.get("details")

        cursor = mydb.cursor()

        try:
            cursor.execute("""
                INSERT INTO complaints (userid, complaint_type, details)
                VALUES (%s, %s, %s)
            """, (userid, complaint_type, details))
            mydb.commit()
            flash("Complaint submitted successfully!", "success")
        except Exception as e:
            mydb.rollback()
            flash(f"Error: {str(e)}")
        finally:
            cursor.close()
            mydb.close()

        return redirect(url_for("complaint"))

     return render_template("complaint.html")       


# Upload settings
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# visitor
@app.route("/visitors", methods=["GET", "POST"])
def visitors():
    if "userid" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    if request.method == "POST":
        userid = session["userid"]
        visitor_name = request.form.get("visitor_name")
        mobile = request.form.get("mobile")
        purpose = request.form.get("purpose")
        visit_time = request.form.get("visit_time")

        picture_file = request.files.get("picture")
        picture_path = None

        if picture_file and allowed_file(picture_file.filename):
            filename = secure_filename(picture_file.filename)
            picture_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            picture_file.save(picture_path)
            picture_path = f"uploads/{filename}"  # save relative path for DB

        cursor = mydb.cursor()

        try:
            cursor.execute("""
                INSERT INTO visitors (userid, visitor_name, mobile, purpose, visit_time, picture)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (userid, visitor_name, mobile, purpose, visit_time, picture_path))
            mydb.commit()
            flash("Visitor added successfully!", "success")
        except Exception as e:
            mydb.rollback()
            flash(f"Error: {str(e)}")
        finally:
            cursor.close()
            mydb.close()

        return redirect(url_for("visitors"))

    return render_template("visitors.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))