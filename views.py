from flask import Flask, request, render_template, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import numpy as np


class Config(object):
    DEBUG = True
    SECRET_KET = '123456'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:123456@localhost/flask_demo"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.secret_key = '123456'
app.config.from_object(Config)
db = SQLAlchemy(app)

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String, nullable=False)
    first_course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    second_course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def __repr__(self):
        return self.name


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/course/add', methods=['GET', 'POST'])
def course():
    if request.method == 'GET':
        course_names = Course.query.all()
        return render_template('course.html', course_names=course_names)

    if request.method == 'POST':
        course_name = request.form.get('course')
        if not all([course_name]):
            flash("请填写课程名")
            return redirect("/course/add")
        c_name = Course.query.filter(Course.name == course_name).first()
        if c_name:
            flash("已存在课程")
            return redirect('/course/add')
        else:
            name = Course(name=course_name)
            try:
                db.session.add(name)
                db.session.commit()
            except Exception as e:
                print(str(e))
                db.session.rollback()
                flash('添加失败')
        return redirect('/')


@app.route("/enrollment/view", methods=['GET', 'POST'])
def student_logon():
    if request.method == 'GET':
        course_names = Course.query.all()
        return render_template('student.html', course_names=course_names)

    if request.method == 'POST':
        s_name = request.form.get('name')
        s_age = request.form.get('age')
        s_email = request.form.get('email')
        fro_email = str(s_email).split("@")
        s_course = request.form.getlist('course_name')
        if not all([s_name]) or not all([s_age]) or not all([s_email]) or len(s_course) == 0:
            flash("请填写信息并选择课程")
            return redirect("/enrollment/view")
        if len(s_course) != 2:
            flash("请选择两门课程")
            return redirect("/enrollment/view")
        if len(fro_email) == 2:
            bac_email = fro_email[1].split(".")
            if len(bac_email) != 2:
                flash("请输入正确的邮箱")
                return redirect("/enrollment/view")
        else:
            flash("请输入正确的邮箱")
            return redirect("/enrollment/view")
        if int(s_age) < 0 or int(s_age) > 120:
            flash("请输入正确的年龄")
            return redirect("/enrollment/view")
        for _id in s_course:
            c_id = Course.query.filter(Course.id != int(_id)).first()
            if not c_id:
                flash("课程不存在")
                return redirect("/enrollment/view")

        student = Student()

        student.name = s_name
        student.age = s_age
        student.email = s_email
        student.first_course_id = int(s_course[0])
        student.second_course_id = int(s_course[1])

        try:
            db.session.add(student)
            db.session.commit()
        except Exception as e:
            print(str(e))
            db.session.rollback()
            flash('添加失败')
        return redirect('/')


@app.route("/enrollment/statistic", methods=['GET'])
def count():
    if request.method == 'GET':
        info = []
        people_count = []
        course_names = Course.query.all()
        for c_name in course_names:
            age = []
            f_result = Student.query.filter(Student.first_course_id == c_name.id).all()
            s_result = Student.query.filter(Student.second_course_id == c_name.id).all()
            f_result.extend(s_result)
            people_count.append(len(f_result))
            for s_name in f_result:
                age.append(s_name.age)
            avg_age = np.mean(age)
            info.append({'name': c_name.name, 'count': len(f_result), 'age': avg_age})

        return render_template('count.html', counts=info)


if __name__ == '__main__':
    app.run()
