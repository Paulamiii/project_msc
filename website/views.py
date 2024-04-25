import os
from flask import Blueprint, render_template, request, flash, jsonify,redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Medicine, Reminder
from . import db
import json
import tensorflow as tf
import easyocr
import numpy as np
from PIL import Image
from fuzzywuzzy import fuzz  

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import datetime



#Initialization Section
#----------------------------------------------------------------

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'


views = Blueprint('views', __name__)

UPLOAD_FOLDER = os.path.join('website', 'uploads')  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#----------------------------------------------------------------




#Routes Section
#----------------------------------------------------------------

@views.route('/')
def index():
    return render_template("index.html", user=current_user)


@views.route('/contact')
def contact():
    return render_template("contact.html", user=current_user)

@views.route('/signin')
def signin():
    return render_template("login.html", user=current_user)

@views.route('/signup')
def signup():
    return render_template("sign_up.html", user=current_user)

@views.route('/results')
def results():
    return render_template("results.html", result=None,user=current_user)

#----------------------------------------------------------------


#Authentication Section
#----------------------------------------------------------------

@views.route('/signupdetails', methods=['GET', 'POST'])
def signupdetails():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('name')
        password1 = request.form.get('password')
        password2 = request.form.get('confirm_password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            print("Account created!")
            return render_template("login.html", user=current_user)


    return render_template("sign_up.html", user=current_user.first_name)

@views.route('/signindetails', methods=['GET', 'POST'])
def signindetails():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.index'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html")


@views.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('views.index'))

#----------------------------------------------------------------


#Upload Section
#----------------------------------------------------------------
@views.route('/upload')
@login_required
def upload():
    return render_template("upload.html", user=current_user)


def preprocess(image):
    image = image.resize((100, 32))  # Resize to model's input size
    image = np.array(image) / 255.0  # Normalize pixel values
    image = image[np.newaxis, ...]    # Add batch dimension
    return image

def process_file(file_path):
    reader = easyocr.Reader(['en'], gpu=False)  # Initialize EasyOCR reader with English language support

    image = Image.open(file_path)

    # Perform handwriting recognition
    result = reader.readtext(image)
    # Extract recognized text from result
    #recognized_text = ' '.join([text for text, _, _ in result])  # Remove unnecessary list comprehension
    extracted_texts = ' '.join([str(item[1]) for item in result])
    
    list_of_strings = extracted_texts.split()

    print("The Extracted Strings are : ",list_of_strings)

    return list_of_strings


def get_medicine(extracted_medicines, accuracy_threshold=80):
    # Get all medicine objects from the database
    all_medicines = Medicine.query.all()

    # List to store tuples of medicine details
    medicine_details = []

    # Iterate through each extracted medicine name
    for extracted_text in extracted_medicines:
        # Clean the extracted text (remove special characters, etc.)
        cleaned_extracted_text = extracted_text.replace("$", "").replace("*", "").replace("**", "")
        
        # List to store tuples of medicine details for the current extracted medicine
        extracted_medicine_details = []

        # Iterate through each medicine in the database
        for medicine in all_medicines:
            # Calculate similarity score between the cleaned extracted text and medicine name
            similarity_score = fuzz.token_sort_ratio(cleaned_extracted_text, medicine.name)
            
            # If similarity score is above the threshold, add medicine details to the list
            if similarity_score >= accuracy_threshold:
                extracted_medicine_details.append((medicine.id, medicine.name, medicine.pack_size))

        # Add medicine details for the current extracted medicine to the main list
        medicine_details.append(extracted_medicine_details)

    return medicine_details




@views.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        print("File path:", file_path)  
        file.save(file_path)
        result = process_file(file_path)

        found_medicines = get_medicine(result)
        print(found_medicines)
        return render_template('results.html', result=found_medicines, user=current_user)  

    return "Invalid file type or filename"

#----------------------------------------------------------------

#Reminder Section
#----------------------------------------------------------------


@views.route('/reminder', methods=['GET', 'POST'])
@login_required
def reminder(): 
    reminder_meds = Reminder.query.filter_by(user_id=current_user.id).all()
    reminder_data = [(reminder.id, reminder.medicine_name, reminder.pack_size) for reminder in reminder_meds]
    print(reminder_data)
    return render_template("404.html", result=reminder_data, user=current_user)

#send email 

def send_email(task, email):
    sender_email = "yourtask24x7@gmail.com"  # Replace with your email
    receiver_email =email
    password = "uwdn edhh wwoc dgcv"  # Replace with your email password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Reminder: Task Due"

    body = f"Hello,\n\nThis is a reminder that you should take '{task}'  now.\n\nRegards,\nYour medicine Reminder"

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())



def check_tasks():
    now = datetime.datetime.now().time()
    for task in tasks:
        task_time = datetime.datetime.strptime(task['time'], '%H:%M').time()
        if now.hour == task_time.hour and now.minute == task_time.minute:
            send_email(task['task'], task['email'])


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_tasks, trigger="interval", seconds=60)
scheduler.start()

tasks=[]

@views.route('/addreminder',methods=['POST'])
def addreminder():
    if request.method == 'POST':
        email=current_user.email
        data = request.json  # Extract JSON data from the request
        selected_medicines = []
        for row in data:
            selected_medicines.append((int(row['id']),row['medicineName'],row['packetSize']))
            tasks.append({'task':row['medicineName'] , 'time':row['addtime'], 'email': email})
            print(row['addtime'])
            print(type(row['addtime']))
            
        print(selected_medicines)
        print(tasks)

        if current_user.is_authenticated:
            for medicine in selected_medicines:
                    reminder = Reminder(id=medicine[0],user_id=current_user.id, medicine_name=medicine[1], pack_size=medicine[2])
                    db.session.add(reminder)
            # Commit the changes to the database
            db.session.commit()
            print("Data Added to database")
            # Redirect to a success page or another appropriate route
        
            
        else:
            # Handle case where user is not authenticated
            return render_template("login.html", user=current_user)
    
    return redirect(url_for("views.reminder"))
    
#----------------------------------------------------------------