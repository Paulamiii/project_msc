import os
from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Note
from . import db
import json
import tensorflow as tf
import easyocr
import numpy as np
from PIL import Image

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'


views = Blueprint('views', __name__)

UPLOAD_FOLDER = os.path.join('website', 'uploads')  # Use os.path.join for file path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')
        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')
    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    return jsonify({})

@views.route('/upload')
def upload():
    return render_template("upload.html")
# Define pre-processing transformations
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
    print(result)
    # Extract recognized text from result
    #recognized_text = ' '.join([text for text, _, _ in result])  # Remove unnecessary list comprehension
    extracted_texts = ' '.join([str(item[1]) for item in result])
    
    return extracted_texts

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
        return render_template('results.html', result=result)

    return "Invalid file type or filename"