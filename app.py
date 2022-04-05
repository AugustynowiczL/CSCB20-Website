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
    type = db.Column(db.String(30), nullable = False)
    reason = db.Column(db.String(500), nullable = False)

@app.route('/')
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        register_details = (
            request.form['user_login'],
            request.form['user_password'],
            request.form['select_user']
        )
        if (register_user(register_details) == 1):
            return render_template('login.html')
        else:
            return render_template('register.html')
    
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    else:
        login_details = (
            request.form['user_login'],
            request.form['user_password']
        )
        if(login_user(login_details) == 1):
            session["name"] = login_details[0]
            session["type"] = Person.query.filter_by(username=login_details[0]).first().type
            return render_template('index.html')
        else:
            return render_template('login.html')


@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/tests')
def tests():
    return render_template('tests.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/labs')
def labs():
    return render_template('labs.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/courseteam')
def courseteam():
    return render_template('courseteam.html')

@app.route('/assignments')
def assignments():
    return render_template('assignments.html')

@app.route('/anonfeedback', methods =  ['GET', 'POST'])
def anonfeedback():
    #query for all teachers, and make a spinner to select on
    query = Person.query.filter_by(type = 'Teacher').all()
    teacher_list = []
    for teacher in query:
        teacher_list.append(teacher.username)

    if request.method == 'GET':
        return render_template('anonfeedback.html', teachers = teacher_list)
    else:
        message = request.form['fname']
        if (len(message) >= 10):
            feedback = Feedback(
                id = Feedback.query.count() + 1,
                feedback = request.form['fname'],
                teacher = request.form['select-teacher']
            )
            db.session.add(feedback)
            db.session.commit()
            return render_template('anonfeedback.html', teachers = teacher_list)
        else:
            flash('Please enter feedback that is at least 10 characters long.', 'error')
            return render_template('anonfeedback.html', teachers = teacher_list)


@app.route('/lectures')
def lectures():
    return render_template('lectures.html')
#query for stduent grades
def query_student_grades():
    query_grades = Student.query.filter_by(username = session['name']).all()
    return query_grades


#make student grades page
@app.route('/student_grades', methods = ['GET','POST'])
def student_grades():
    query_grades = query_student_grades()
    if request.method == 'GET':
        return render_template('student_grades.html', q = query_grades)
    else:
        print(request.form['select-assignment'])
        print(request.form['fname'])
        remark = Remark(
            username = session['name'],
            type = request.form['select-assignment'],
            reason = request.form['fname']
        )
        db.session.add(remark)
        db.session.commit()
        return render_template('student_grades.html', q = query_grades)
        
#query for teacher grades
def query_teacher_grades():
    query_grades = Student.query.all()
    return query_grades

#query a specific student passed
def query_student(username):
    return Student.query.filter_by(username = username).first()

#query all student remarks
def query_teacher_remarks():
    return Remark.query.all()

@app.route('/teacher_grades',methods = ['GET','POST'])
def teacher_grades():
    query_remarks = query_teacher_remarks()
    if request.method =='GET':
        query_grades = query_teacher_grades()
        return render_template('teacher_grades.html', q = query_grades, remarks = query_remarks)
    else:
        grade_details = (
            request.form['select-student'],
            request.form['select-type'],
            request.form['grade-input']
        )
        if (not grade_details[2]):
            query = query_teacher_grades()
            return render_template('teacher_grades.html', q = query, remarks = query_remarks)
        student = query_student(grade_details[0])
        if (grade_details[1] == "Midterm"):
            student.midterm = grade_details[2]
        elif (grade_details[1] == "Assignment"):
            student.assignment = grade_details[2]
        student.average = ((float(student.midterm) + float(student.assignment))/2.0)
        db.session.commit()
        query = query_teacher_grades()
        return render_template('teacher_grades.html', q = query, remarks = query_remarks)


@app.route('/teacher_feedback',methods = ['GET','POST'])
def teacher_feedback():
    if request.method == 'GET':
        query = Feedback.query.filter_by(teacher = session['name'])
        return render_template('teacher_feedback.html', q = query)

@app.route('/logout')
def logout():
    session.pop('name', default = None)
    session.pop('type', default = None)
    return render_template('login.html') 

def register_user(register_details):
    person = Person.query.filter_by(username=register_details[0]).first()
    if person:
        flash('There already exists this username. Try again', 'error')
        return 0
    userusername = register_details[0]
    userpassword = register_details[1]
    if userpassword and userusername:
        hashed = bcrypt.generate_password_hash(userpassword).decode('utf-8')
        person = Person(username = register_details[0], password = hashed, type = register_details[2])
        student = Student(username = register_details[0], midterm = 0, assignment = 0, average = 0)
        db.session.add(person)
        db.session.add(student)
        db.session.commit()
        return 1
    else:
        return 0
 
def login_user(login_details):
    person = Person.query.filter_by(username=login_details[0]).first()
    if login_details[1] and login_details[0]:    #check to make sure field is not blank so that we do not get a null error
        if not person or not bcrypt.check_password_hash(person.password, login_details[1]):
            flash('Please check your login details and try again', 'error')
            return 0
        return 1
    return 0


if __name__ == '__main__':
    app.run(debug=True)

