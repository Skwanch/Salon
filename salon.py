import time
import os
import datetime as dt
from datetime import datetime, timedelta
from hashlib import md5
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash

from models import db, Owner, Stylist, Patron, Appointment

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(app.root_path, 'salon.db')

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_object(__name__)
app.config.from_envvar('SALON_SETTINGS', silent=True)
app.debug = True

db.init_app(app)

@app.cli.command("initdb")
def init_db():
    db.drop_all()
    db.create_all()
    owner = Owner()
    db.session.add(owner)
    db.session.commit()
    print('Initialized the database')

def get_patron_id(username):
    """Convenience method to look up the id for a username."""
    rv = Patron.query.filter_by(username=username).first()
    return rv.patron_id if rv else None

def get_stylist_id(username):
    """Convenience method to look up the id for a username."""
    rv = Stylist.query.filter_by(username=username).first()
    return rv.stylist_id if rv else None

@app.before_request
def before_request():
    g.patron = None
    if 'patron_id' in session:
        g.patron = Patron.query.filter_by(patron_id=session['patron_id']).first()
    g.stylist = None
    if 'stylist_id' in session:
        g.stylist = Stylist.query.filter_by(stylist_id=session['stylist_id']).first()
    g.owner = None
    if 'owner_id' in session:
        g.owner = Owner.query.filter_by(owner_id=session['owner_id']).first()


# by default, direct to login
@app.route("/")
def default():
    return redirect(url_for("login"))
    
@app.route("/login/", methods=["GET", "POST"])
def login():
    if g.patron:
        return redirect(url_for('patron_profile', username = g.patron.username))
    if g.stylist:
        return redirect(url_for('stylist_profile', username = g.stylist.username))
    if g.owner:
        return redirect(url_for('owner_profile'))
    error=None
    if request.method == 'POST':
        patron = Patron.query.filter_by(username=request.form['user']).first()
        stylist = Stylist.query.filter_by(username=request.form['user']).first()
        if patron is None:
            if stylist is None:
                if request.form['user'] == 'owner':
                    if request.form['pass'] == 'pass':
                        print('owner login')
                        flash('Log in successful')
                        session['owner_id'] = Owner.query.first().owner_id
                        return redirect(url_for('owner_profile'))
                    else:
                        error = 'Invalid password'
                else:
                    error = 'Invalid username'
            else:
                #Check for correct stylist password
                if stylist.password == request.form['pass']:
                    flash('Log in successful')
                    session['stylist_id'] = stylist.stylist_id
                    return redirect(url_for('stylist_profile', username=stylist.username))
                else:
                    error = 'Invalid password'    
        else:
            #Check for the correct patron password
            if patron.password == request.form['pass']:
                flash('Log in successful')
                session['patron_id'] = patron.patron_id
                return redirect(url_for('patron_profile', username = patron.username))
            else:
                error = 'Invalid password'
    return render_template('loginPage.html', error=error)

@app.route("/logout/", methods=["GET", "POST"])
def logout():
    if g.patron:
        flash('Logged out')
        session.pop('patron_id', None)
        return redirect(url_for('login'))
    if g.stylist:
        flash('Logged out')
        session.pop('stylist_id', None)
        return redirect(url_for('login'))
    if g.owner:
        flash('Logged out')
        session.pop('owner_id', None)
        return redirect(url_for('login'))
    #If no one is in session, redirect them to the log in page
    else:
        return redirect(url_for('login'))

@app.route("/signup/", methods=['GET', 'POST'])
def signup():
    #If a user is logged in, redirect them to their userpage
    if g.patron:
        return redirect(url_for('patron_profile', username=g.patron.username))
    if g.stylist:
        return redirect(url_for('stylist_profile', username = g.stylist.username))
    if g.owner:
        return redirect(url_for('owner_profile'))
    error = None
    if request.method == 'POST':
        #Check for a username
        if not request.form['user']:
            error = 'Please enter a username'
        #Check for a password
        elif not request.form['pass']:
            error = 'Please enter a password'
        #Check for matching passwords
        elif request.form['pass'] != request.form['pass2']:
            error = 'Passwords do not match'
        #Make sure that username is not taken
        elif get_patron_id(request.form['user']) is not None:
            error = 'The username is already taken'
        #Add the user to the data base
        else:
            db.session.add(Patron(request.form['user'], request.form['pass']))
            db.session.commit()
            flash('Successfully signed up! You can now log in')
            return redirect(url_for('login'))
    return render_template('signup.html', error=error)

@app.route("/owner-profile/")
def owner_profile():
    if g.owner:
        #Check if the user is in session
        if g.owner.username == 'owner':
            stylist_list = Stylist.query.all()
            patron_list = Patron.query.all()
            return render_template('ownerProfile.html', stylists=stylist_list, patrons=patron_list)
        #Throw an error for unathorized users
        else:
            abort(401)
    elif g.stylist:
        abort(401)
    elif g.patron:
        abort(401)
    #If no one is in session, redirect them to the login page
    else:
        redirect(url_for('login'))

#Display stylist profile    
@app.route("/stylist-profile/<username>/")
def stylist_profile(username):
    today = dt.datetime.today()
    date_list = [(today + dt.timedelta(days=x)).date() for x in range(0, 7)]
    hour_list = [(datetime.strptime('10:00AM', '%I:%M%p') + dt.timedelta(hours=x)).time() for x in range(11)] 
    
    if g.patron:
        stylist = Stylist.query.filter_by(username=username).first()
        return render_template('stylistProfile.html', stylist = stylist.username, username = g.patron.username, usertype = "patron", appts = stylist.appointments, dates = date_list, hours = hour_list)
    if g.owner:
        stylist = Stylist.query.filter_by(username=username).first()
        return render_template('stylistProfile.html', usertype = "owner", appts = stylist.appointments, dates = date_list, hours = hour_list)
    if g.stylist:
        if g.stylist.username == username:
            return render_template('stylistProfile.html', usertype = "stylist", appts = g.stylist.appointments, dates = date_list, hours = hour_list)
        else:
            stylist = Stylist.query.filter_by(username=username).first()
            return render_template('stylistProfile.html', usertype = "stylist", appts = stylist.appointments, dates = date_list, hours = hour_list)

#Display patron profile
@app.route("/patron-profile/<username>/")
def patron_profile(username):
    stylist_list = Stylist.query.all()
    if g.patron:
        if g.patron.username == username:
            return render_template('patronProfile.html', username = g.patron.username, appts = g.patron.appointments, stylists = stylist_list)
        else:
            abort(401)
    elif g.stylist:
        patron = Patron.query.filter_by(username=username).first()
        return render_template('patronProfile.html', appts = patron.appointments, stylists = stylist_list)
    elif g.owner:
        patron = Patron.query.filter_by(username=username).first()
        return render_template('patronProfile.html', appts = patron.appointments, stylists = stylist_list)
    else:
        return redirect(url_for('login'))

@app.route("/schedule-appointment/<date>+<time>+<username>+<stylist>", methods=['GET', 'POST'])
def schedule_appt(date, time, username, stylist):
    if g.patron:
        if g.patron.username == username:

            stylist = Stylist.query.filter_by(username=stylist).first()
            date = datetime.strptime(date, '%Y-%m-%d')
            time = datetime.strptime(time, '%H:%M:%S').time()
            datetime_obj = dt.datetime.combine(date, time)

            appt = Appointment(datetime_obj)#, get_stylist_id(stylist), g.patron.patron_id)
            appt.patron_id = g.patron.patron_id
            appt.stylist_id = stylist.stylist_id

            g.patron.appointments.append(appt)
            stylist.appointments.append(appt)
            db.session.add(appt)
            db.session.commit()
            flash('Appointment scheduled')
            return redirect(url_for('patron_profile', username = g.patron.username))
    if g.stylist:
        abort(401)
    if g.owner:
        abort(401)

@app.route("/cancel-appointment-<ID>/", methods=['GET', 'POST'])
def cancel_appt(ID):
    if not ID:
        abort(401)
    if g.patron:
        appt = Appointment.query.filter_by(appt_id = ID).first()
        if not appt:
            abort(404)
        patron = appt.patron_id
        if g.patron.patron_id != patron:
            abort(404)
        db.session.delete(appt)
        db.session.commit()
        return render_template('cancel.html')
    if g.stylist:
        abort(401)
    if g.owner:
        abort(401)

@app.route("/create-stylist-account/", methods=['GET', 'POST'])
def create_stylist():
    if g.owner:
        error = None
        if request.method == 'POST':
            if not request.form['user']:
                error = 'Please enter a username'
            elif not request.form['pass']:
                error = 'Please enter a password'
            elif request.form['pass'] != request.form['pass2']:
                error = 'Passwords do not match'
            elif get_stylist_id(request.form['user']) is not None:
                error = 'Username is already taken'
            else:
                db.session.add(Stylist(request.form["user"], request.form["pass"]))
                db.session.commit()
                flash('Stylist successfully registered')
                return redirect(url_for('owner_profile'))
            return render_template('createStylist.html', error=error)
        else:
            return render_template('createStylist.html', error=error)
    else:
        abort(401)

app.secret_key = "fhqwhgads"

'''
@app.cli.command("bootstrap")
def bootstrap_data():
    """Populates database with data"""
    db.drop_all()
    db.create_all()

    owner = Owner("owner", "pass")

    db.session.add(owner)

    db.session.commit()

    print("Added dataset")
'''


