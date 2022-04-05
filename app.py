from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__, template_folder = 'templates', static_folder='static')
app.secret_key = b"secretkey"
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class Person(db.Model):
    __tablename__ = 'Person'
    username = db.Column(db.String(100), unique = True, nullable=False, primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), nullable=False)

class Student(db.Model):
    __tablename__ = 'Student'
    username = db.Column(db.String(100),unique = True,nullable = False, primary_key = True)
    midterm = db.Column(db.Float, unique = False, nullable = True)
    assignment = db.Column(db.Float, unique = False, nullable = True)
    average = db.Column(db.Float, unique = False, nullable = True)

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    id = db.Column(db.Integer, primary_key = True)
    feedback = db.Column(db.String(280))
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.today)
    teacher = db.Column(db.String(20),unique = True,nullable = False)

class Remark(db.Model):
    __tablename__ = 'Remark'
    username = db.Column(db.String(100), primary_key = True)
    type = db.Column(db.String(30), primary_key = True)
    reason = db.Column(db.String(500), nullable = False)


@app.route('/')
@app.route('/register', methods = ['GET', 'POST'])  #register page
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        register_details = (        # store the form into a tuple
            request.form['user_login'],
            request.form['user_password'],
            request.form['user_confirm_password'],
            request.form['select_user']
        )
        if (register_user(register_details) == 1):      #send to helper, 1 if successful register, 0 if unsuccessful
            return render_template('login.html')        #if successful send to login screen
        else:
            return render_template('register.html')     #if successful stay on register page

#login page
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    else:
        login_details = (
            request.form['user_login'],
            request.form['user_password']       #store login in tuple
        )
        if(login_user(login_details) == 1):     #helper to check if valid login
            session["name"] = login_details[0]
            session["type"] = Person.query.filter_by(username=login_details[0]).first().type    #if so add too session and send them to main page
            return render_template('index.html')
        else:   
            return render_template('login.html')        #if not valid login then stay on login page

#calendar page
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

#resources page
@app.route('/resources')
def resources():
    return render_template('resources.html')

#tests page
@app.route('/tests')
def tests():
    return render_template('tests.html')

#news page
@app.route('/news')
def news():
    return render_template('news.html')

#labs page
@app.route('/labs')
def labs():
    return render_template('labs.html')

#index page
@app.route('/index')
def index():
    return render_template('index.html')

#courseteam page
@app.route('/courseteam')
def courseteam():
    return render_template('courseteam.html')

#assignment page
@app.route('/assignments')
def assignments():
    return render_template('assignments.html')

#anon feedback page
@app.route('/anonfeedback', methods =  ['GET', 'POST'])
def anonfeedback():
    #query for all teachers, and make a spinner to select on
    query = Person.query.filter_by(type = 'Teacher').all()
    teacher_list = []
    for teacher in query:
        teacher_list.append(teacher.username)       #store all teachers in an array

    if request.method == 'GET':
        return render_template('anonfeedback.html', teachers = teacher_list)        #get request just shows the page and has drop down with the list of teacher    
    else:
        message = request.form['fname']         
        if (len(message) >= 10):
            feedback = Feedback(            #if the feedback is more then 10, then it is valid and create an entry in database
                id = Feedback.query.count() + 1,        #feedback has id based on the # of feedbacks
                feedback = request.form['fname'],
                teacher = request.form['select-teacher']
            )
            db.session.add(feedback)
            db.session.commit()
            return render_template('anonfeedback.html', teachers = teacher_list)
        else:
            flash('Please enter feedback that is at least 10 characters long.', 'error')        #if the feedback is not >=10 then not valid and flash message
            return render_template('anonfeedback.html', teachers = teacher_list)

#lectures page
@app.route('/lectures')
def lectures():
    return render_template('lectures.html')

#query for stduent grades
def query_student_grades():
    query_grades = Student.query.filter_by(username = session['name']).all()        #helper to query the logged in students grades
    return query_grades

def query_student_remarks():
    query_student_remarks = Remark.query.filter_by(username = session['name']).all()
    return query_student_remarks

#make student grades page
@app.route('/student_grades', methods = ['GET','POST'])
def student_grades():
    query_grades = query_student_grades()       #query for student grades 
    query_remarks = query_student_remarks()     #query the current logged in students remarks
    if request.method == 'GET':
        return render_template('student_grades.html', q = query_grades, r = query_remarks)     #if get request, just show the students grades
    else:
        print(request.form['select-assignment'])        
        print(request.form['fname'])
        remark = Remark(                    #if a post request, means student wants a remark, store all information in a database class, and add it to database
            username = session['name'],
            type = request.form['select-assignment'],
            reason = request.form['fname']
        )
        for query in query_remarks:
            if remark.type == query.type:
                flash('You already have an outstanding remark request', 'error')
                return render_template('student_grades.html', q = query_grades, r = query_remarks)
        db.session.add(remark)
        db.session.commit()
        query_remarks = query_student_remarks() 
        return render_template('student_grades.html', q = query_grades, r = query_remarks)
        
#query for teacher grades
def query_teacher_grades():
    query_grades = Student.query.all()      #helper to get all student grades to show on teacher grades page
    return query_grades

#query a specific student passed
def query_student(username):
    return Student.query.filter_by(username = username).first()     #query the passed students grades and return

#query all student remarks
def query_teacher_remarks():
    return Remark.query.all()           #query all remark requests in database

#teacher grades page
@app.route('/teacher_grades',methods = ['GET','POST'])
def teacher_grades():
    query_remarks = query_teacher_remarks()     #query all remakr requests
    if request.method =='GET':
        query_grades = query_teacher_grades()       #query all the students grades
        return render_template('teacher_grades.html', q = query_grades, remarks = query_remarks)        #if get request just show all student grades and remarks
    else:
        grade_details = (                       #if post, then teacher is manually changing a students grades, store it in tuple
            request.form['select-student'],
            request.form['select-type'],
            request.form['grade-input']
        )
        if (not grade_details[2]):              #if grade field is blank, then do nothing, just rerender page
            query = query_teacher_grades()
            return render_template('teacher_grades.html', q = query, remarks = query_remarks)
        student = query_student(grade_details[0])           #query the selected students grades
        if (grade_details[1] == "Midterm"):             #if the teacher is changing the students midterm mark, adjust the result accordingly
            student.midterm = grade_details[2]
        elif (grade_details[1] == "Assignment"):    #if the teacher is changing the students assignment mark, adjust the result accordingly
            student.assignment = grade_details[2]
        student.average = ((float(student.midterm) + float(student.assignment))/2.0)            #adjust the average field accordingly
        db.session.commit()             #commit the changes to the db
        query = query_teacher_grades()          #re query the grades to ensure that the updated mark is shown
        return render_template('teacher_grades.html', q = query, remarks = query_remarks)

#teacher feedback page
@app.route('/teacher_feedback',methods = ['GET','POST'])
def teacher_feedback():
    if request.method == 'GET':
        query = Feedback.query.filter_by(teacher = session['name'])     #query all the feedback for logged in teacher via session
        return render_template('teacher_feedback.html', q = query)

#logout page
@app.route('/logout')
def logout():
    session.pop('name', default = None)         #logout, just pops the current logged in users name and type
    session.pop('type', default = None)
    return render_template('login.html') 

#helper function to properly register a user
def register_user(register_details):
    person = Person.query.filter_by(username=register_details[0]).first()
    if person:
        flash('There already exists this username. Try again', 'error')             #if the username already, flash message and error
        return 0
    userusername = register_details[0]
    userpassword = register_details[1]
    userconfirmpassword = register_details[2]           #store the forms details
    if userpassword and userusername:           #ensure that username and password fields arent blank
        if (userpassword == userconfirmpassword):       #ensure two passwords match
            hashed = bcrypt.generate_password_hash(userpassword).decode('utf-8')        #hash the password
            person = Person(username = register_details[0], password = hashed, type = register_details[3])      #create entry in db
            db.session.add(person)
            if(register_details[3] == "Student"):       #if the type is student, also initalize his grades to 0's
                student = Student(username = register_details[0], midterm = 0, assignment = 0, average = 0) #add students grades entry to db
                db.session.add(student)
            db.session.commit()     #commit db
            return 1
        else:
            flash('Passwords do not match.', 'error')       #if the passwords do not match flash message
            return 0
    else:
        flash('Cannot have empty fields', 'error')  #if fields are empty flash message
        return 0
 
#helper to check if the entered credentials exist in database
def login_user(login_details):
    person = Person.query.filter_by(username=login_details[0]).first()      #query user based on arguments passed
    if login_details[1] and login_details[0]:    #check to make sure field is not blank so that we do not get a null error
        if not person or not bcrypt.check_password_hash(person.password, login_details[1]):     #check to make sure that entered password matches hashed password in database
            flash('Please check your login details and try again', 'error')     #if passwords do not match then flash message and do not login 
            return 0
        return 1
    return 0


if __name__ == '__main__':
    app.run(debug=True)

