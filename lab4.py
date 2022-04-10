from flask import Flask, url_for, render_template, request, send_from_directory, g, abort, flash, session
from flask_session import Session
from werkzeug.utils import redirect, secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import sqlite3
import os
import uuid
import loginform
from flask_login import LoginManager, login_user
from FDataBase import FDataBase
from UserLogin import UserLogin
from flask_sqlalchemy import SQLAlchemy



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'flsite.db'
DEBUG = True
SECRET_KEY = '&8\xa2|\x11\x0f\xcf\xe8\xc2\xa6\x85"\xfd~\x0c#\x06{>T\xb7\xe9\xd8\xc9'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
app.config['SESSION_PEMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///blog.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
login_manager = LoginManager(app)
dbalc = SQLAlchemy(app)

class Users(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key = True)
    name = dbalc.Column(dbalc.String(50), nullable = True)
    surname = dbalc.Column(dbalc.String(50), nullable=True)
    email = dbalc.Column(dbalc.String(50), unique = True)
    age = dbalc.Column(dbalc.Integer, nullable = True)
    work = dbalc.Column(dbalc.String(50), nullable = True)
    post = dbalc.Column(dbalc.String(50), nullable=True)
    password = dbalc.Column(dbalc.String(500), nullable = True)
    photo = dbalc.Column(dbalc.String(500), nullable=True)
    role = dbalc.Column(dbalc.String(50), nullable=True)

class News(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key=True)
    maintext = dbalc.Column(dbalc.String(5000), nullable=True)
    category = dbalc.Column(dbalc.String(100), dbalc.ForeignKey('categories.category'))
    user_id = dbalc.Column(dbalc.Integer, dbalc.ForeignKey('users.id'))

class Categories(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key=True)
    category = dbalc.Column(dbalc.String(100), nullable=True)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    db=connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/registration/', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        create_db()
        file = request.files['photo']
        if file and allowed_file(file.filename):
            s = uuid.uuid4()
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(s) + '.jpg'))
            filename2db = str(s) + '.jpg'

            db = get_db()
            dbase = FDataBase(db)

            try:
                if request.form.get('named') == 'admin':
                    if Users.query.filter_by(name = request.form.get('named')).first():
                        flash("Не пытайтесь добавить еще одного админа!")
                        return redirect(url_for('register'))
                else:
                    u = Users(name=request.form.get('named'), surname=request.form.get('surname'),
                              email=request.form.get('email'),
                              age=request.form.get('age'),
                              work=request.form.get('work'), post=request.form.get('position'),
                              password=generate_password_hash(request.form.get('password')), photo=filename2db,
                              role='Админ')
                    dbalc.session.add(u)
                    dbalc.session.flush()
                    dbalc.session.commit()
                    return redirect(url_for('users') + '?page=0')

                u = Users(name = request.form.get('named'), surname = request.form.get('surname'), email = request.form.get('email'),
                          age = request.form.get('age'),
                          work = request.form.get('work'), post = request.form.get('position'),
                          password = generate_password_hash(request.form.get('password')), photo = filename2db, role = 'Пользователь')
                dbalc.session.add(u)
                dbalc.session.flush()
                dbalc.session.commit()
            except:
                dbalc.session.rollback()
                print("ОШИБКА ДОБАВЛЕНИЯ пользователя!")
            return redirect(url_for('users')+'?page=0')


@app.route('/uploads/<name>')
def download_file(name):
    redirect(url_for('users')+'?page=1')

@app.route('/users/')
def users():

    db = get_db()
    dbase = FDataBase(db)
    id_sess = ""
    curr_page = int(request.args.get('page'))
    pgcount = 1
    remainder = 0
    all_users = Users.query.all()
    pgcount = len(all_users) // 4 + 1
    if pgcount == 0:
        pgcount = 1
    if curr_page > pgcount:
        abort(404)
    if pgcount % 4 > 0:
        remainder = len(all_users) % 4
    class pgstore:
        value = pgcount
    match curr_page:
        case 0:
            a = all_users[:4]
        case pgstore.value:
            a = all_users[pgcount - 1:remainder]
        case _:
            a = all_users[curr_page * 4:curr_page * 4 + 4]
    try:
        id_sess = session['login']
    except:
        pass
    return render_template('users.html', users=a, curr_page=curr_page, pagecount=pgcount, id_sess=id_sess)

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    dbase = FDataBase(db)
    return UserLogin().fromDB(user_id, dbase)

@app.route('/auth/', methods=['POST', 'GET'])
def auth():
    db = get_db()
    dbase = FDataBase(db)
    form1 = loginform.LoginForm()
    if request.method == 'POST':
        user = dbase.getUserByEmail(request.form.get('username'))
        u = Users.query.filter_by(email = request.form.get('username')).first()
        if u and check_password_hash(u.password, request.form.get('password')):
            session['login'] = u.email
            return redirect(url_for('users')+'?page=0')
        flash("Неверный логин/пароль")
        return render_template('auth.html', form=form1, user=user)
    else:
        if request.args.get('avt') is not None:
            session.pop('login')
        if 'login' in session:
            u = Users.query.filter_by(email = session['login']).first()
            return render_template('auth.html', form=form1, user=u)
        return render_template('auth.html', form=form1)

@app.route('/account/', methods=['POST', 'GET'])
def account():
    is_adm = False
    db = get_db()
    dbase = FDataBase(db)
    if request.method == 'POST':
        user = Users.query.filter_by(email = request.args.get('user')).first()
        user.name = request.form.get('names')
        user.surname = request.form.get('surname')
        dbalc.session.commit()
        return redirect(url_for('users') + '?page=0')
    form1 = loginform.LoginForm()
    if 'login' in session:
        user = Users.query.filter_by(email = request.args.get('user')).first()
        if user:
            if( Users.query.filter_by(email = session['login']).first().role == 'Админ'):
                is_adm = True
            return render_template('account.html', user=user, id_sess=session['login'], is_adm=is_adm)
        else:
            abort(404)
    else:
        flash("Авторизируйтесь, чтобы просматривать аккаунты")
        return redirect(url_for('users') + '?page=0')

@app.route('/news/', methods=['POST', 'GET'])
def news():
    if 'login' not in session:
        flash("Авторизируйтесь, чтобы просматривать и добавлять новости")

    return render_template('news.html')

@app.route('/news/addnews', methods=['POST', 'GET'])
def add_news():
    if 'login' in session:
        if request.method == 'POST':
            pass

        cati = Categories.query.all()
        spis_cati = []
        for i in range(len(cati)):
            spis_cati.append(cati[i].category)
        user = Users.query.filter_by(email=session['login']).first()
        return render_template('addnews.html', cati=spis_cati, user=user)
    else:
        return redirect(url_for('news'))

@app.route('/news/addcat/', methods=['POST', 'GET'])
def add_cat():
    if 'login' in session:
        if Users.query.filter_by(email=session['login']).first().role == 'Админ':
            if request.method == 'POST':
                new_c = Categories(category = request.form.get('new_category'))
                dbalc.session.add(new_c)
                dbalc.session.flush()
                dbalc.session.commit()
            return render_template('addcat.html')
        else:
           return redirect(url_for('add_news'))
    else:
        return redirect(url_for('news'))

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
