from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, redirect, url_for

from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), nullable=False)
    todo = db.relationship('Todo', backref='user')


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    uniq_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Task %r>' % self.id


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    confirm_password = PasswordField('confirm password', validators=[InputRequired()])

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if form.password.data == user.password :
            #if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))

        #return redirect('/signup')
        #return '<h1>' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
       #hashed_password = generate_password_hash(form.password.data, method='sha256')
       new_user = User(email=form.email.data, password=form.password.data)
       db.session.add(new_user)
       db.session.commit()
       return redirect('/login')
        #return '<h1>' + form.confirm_password.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'
    
    return render_template('signup.html', form = form)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if request.method == 'POST':
        task_content =request.form['content']
        task_status = request.form['status']
        new_task = Todo(content=task_content,status=task_status,uniq_id=current_user.id)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'

    else:
        tasks = Todo.query.filter_by(uniq_id=current_user.id).all()
        #tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.status = request.form['status']
        db.session.commit()
        return redirect('/')

    else:
        return render_template('update.html', task=task)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)