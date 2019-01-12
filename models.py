from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Classes
class Owner(db.Model):
    owner_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80), unique=True)

    def __init__(self):
        self.username = "owner"
        self.password = "pass"

class Stylist(db.Model):
    stylist_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120), unique=True)
    appointments = db.relationship('Appointment', backref= db.backref('stylist', lazy='joined'), lazy='select')
    

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Patron(db.Model):
    patron_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120), unique=True)
    appointments = db.relationship('Appointment', backref= db.backref('patron', lazy='joined'), lazy='select')

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Appointment(db.Model):
    appt_id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    stylist_id = db.Column(db.Integer, db.ForeignKey('stylist.stylist_id'))
    patron_id = db.Column(db.Integer, db.ForeignKey('patron.patron_id'))

    def __init__(self, datetime): 
        self.datetime = datetime
 

