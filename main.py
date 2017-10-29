from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi
import os
import jinja2

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(240))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner_id):
        self.title = title
        self.body = body
        self.completed = False
        self.owner_id = owner_id

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password
        

def get_blogs():
    return Task.query.all()

def get_users():
    return User.query.all()

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'index']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user in get_users():
            if user.password == password:
                session['email'] = email
                session['owner_id'] = user.id
                flash("Logged in")
                return redirect('/newpost')
            else:
                flash('User password incorrect', 'error')
                return redirect('/login')
        else:
            flash('User does not exist', 'error')
            return redirect('/login')

    return render_template('login.html', title="Log In")



@app.route('/blog', methods=['GET'])
def list_blogs():
    id = request.args.get('id')
    user = request.args.get('user')

    if id == None:
        if user == None:
            return render_template('todos.html', 
            task=get_blogs(), user=get_users())  
        else:
            user = int(user)
            return render_template('userblogs.html', 
            user=user, task=get_blogs())    
    else:
        id = int(id)
        return render_template('displayblog.html', 
        task=get_blogs(), id=id, user=get_users())


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        if (email.strip() == ""):
            flash("Please enter a valid email", "error")
            return redirect('/register')
        else:
            if len(email) < 3:
                flash("Email must contain at least 3 characters. Please enter a valid username", 
                "error")
                return redirect('/register')

        if (password.strip() == ""):
            flash("Please enter a valid password", "error")
            return redirect('/register')
        else:
            if len(password) < 3:
                flash("Password must contain at least 3 characters. Please enter a valid password", 
                "error")
                return redirect('/register')

        if password == verify:
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                new_user = User(email, password)
                db.session.add(new_user)
                db.session.commit()
                session['email'] = email
                return redirect('/newpost')
            else:
                flash('This email is already taken', 'error')
                return redirect ('/register')
        else:
            flash('Passwords do not match', 'error')

    return render_template('register.html')


@app.route('/', methods=['GET'])
def index():
    return render_template('userlist.html', user=get_users())

@app.route('/delete-task', methods=['POST'])
def delete_task():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.add(task)
    db.session.commit()

    return redirect('/blog')



@app.route('/newpost', methods=['POST', 'GET'])
def new_post():

    body_error = ''
    title_error = ''
    blog_body = ''
    blog_title = ''
    blog_owner = session['owner_id']

    if request.method == 'POST':
        blog_title = request.form['blog-title']
        blog_body = request.form['blog-body']

        if blog_title == '':
            title_error = "Enter a valid title"

        if blog_body == '':
            body_error = "Enter a valid body text"

    
        if title_error != '' or body_error != '':
            return render_template('addblog.html', 
            title_error=title_error, 
            body_error=body_error,
            blog_title=blog_title,
            blog_body=blog_body)
        else:
            new_blog = Task(blog_title, blog_body, blog_owner)
            db.session.add(new_blog)
            db.session.commit()

        return redirect('/blog?id={0}'.format(new_blog.id))
                    
        
    return render_template('addblog.html',title="BLOGS")

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/blog')


if __name__ == '__main__':
    app.run()