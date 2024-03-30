from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import keras_ocr

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
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

def process_file(file_path):
    # Load the model paths
    craft_model_path = 'C:/Users/USER/.keras-ocr/craft_mlt_25k.h5'
    crnn_model_path = 'C:/Users/USER/.keras-ocr/crnn_kurapan.h5'

    # Load the image
    image = keras_ocr.tools.read(file_path)

    # Create the OCR pipeline
    detector = keras_ocr.detection.Detector()
    recognizer = keras_ocr.recognition.Recognizer()
    pipeline = keras_ocr.pipeline.Pipeline(detector=detector, recognizer=recognizer)

    # Perform OCR on the image
    prediction_groups = pipeline.recognize(images=[image])

    # Process the OCR results
    result = []
    for predictions in prediction_groups:
        for word_info in predictions:
            word = word_info[0]
            result.append(word)

    return result




@views.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']
    print(file)
    if file.filename == '':
        return "No selected file"

    file_path = f"/uploads/{file.filename}"
    file.save(file_path)

    result = process_file(file_path)  # Call your model function

    return render_template('results.html', result=result)

    if 'image' not in request.files:
        return "No file part"

    image = request.files['image']

    if image.filename == '':
        return "No selected file"


    return "Image uploaded successfully"