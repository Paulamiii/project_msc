from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')
    #doctors=db.relationship('Doctor')

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    pack_size = db.Column(db.String(200), unique=False, nullable=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),primary_key=True, nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    pack_size = db.Column(db.String(200), nullable=False)

'''class Doctor(db.model):
    id=db.Column(db.Integer,primary_key=True)
    doct_name=db.Column(db.String(150))
    doct_contact=db.column(db.Integer,unique=True)
    doct_department=db.Column(db.String(150))
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'))'''
    

    