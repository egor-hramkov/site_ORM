from datetime import datetime
from flask import Flask, url_for, render_template, request, send_from_directory, g, abort, flash, session
from flask_session import Session
from werkzeug.utils import redirect, secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import loginform
from flask_login import LoginManager
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
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///mains.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
login_manager = LoginManager(app)
dbalc = SQLAlchemy(app)

last_cata = ""

class Users(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key = True, autoincrement=True)
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
    id = dbalc.Column(dbalc.Integer, primary_key=True, autoincrement=True)
    maintext = dbalc.Column(dbalc.String(5000), nullable=True)
    category = dbalc.Column(dbalc.String(100))
    date_created = dbalc.Column(dbalc.DateTime, default=datetime.utcnow())
    user_id = dbalc.Column(dbalc.Integer)

class Categories(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key=True, autoincrement=True)
    category = dbalc.Column(dbalc.String(100), nullable=True)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route('/')
def index():
    return redirect(url_for('mainpage'))

@app.route('/mainpage/')
def mainpage():
    return render_template('mainpage.html')

@app.route('/registration/', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        file = request.files['photo']
        if file and allowed_file(file.filename):
            s = uuid.uuid4()
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(s) + '.jpg'))
            filename2db = str(s) + '.jpg'
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
    id_sess = ""
    if not request.args.get('page'):
        abort(404)
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
  pass

@app.route('/auth/', methods=['POST', 'GET'])
def auth():
    form1 = loginform.LoginForm()
    if request.method == 'POST':
        u = Users.query.filter_by(email = request.form.get('username')).first()
        if u and check_password_hash(u.password, request.form.get('password')):
            session['login'] = u.email
            return redirect(url_for('users')+'?page=0')
        flash("Неверный логин/пароль")
        return render_template('auth.html', form=form1, user=u)
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
            news_of_user = News.query.filter_by(user_id = user.id).order_by(News.date_created.desc()).all()

            return render_template('account.html', user=user, id_sess=session['login'], is_adm=is_adm, news_of_user = news_of_user)
        else:
            abort(404)
    else:
        flash("Авторизируйтесь, чтобы просматривать аккаунты")
        return redirect(url_for('users') + '?page=0')

@app.route('/news/', methods=['POST', 'GET'])
def news():
    #all_news = []
    if not request.args.get('page'):
        abort(404)
    if 'login' not in session:
        flash("Авторизируйтесь, чтобы просматривать и добавлять новости")
        return redirect(url_for('auth'))
    else:
        cati = Categories.query.all()
        spis_cati = []
        for i in range(len(cati)):
            spis_cati.append(cati[i].category)
        if request.method == 'POST':
            all_news = News.query.filter_by(category = request.form.get('category_sort')).order_by(News.date_created.desc()).all()
            is_sort = True
        else:
            all_news = News.query.order_by(News.date_created.desc()).all()
            is_sort = False
        if all_news == []:
            flash("Станьте первым, кто выложит новость")
            return render_template('news.html', all_news = all_news, cati = spis_cati)

        user = Users.query.filter_by(id = all_news[0].user_id).first()
        curr_page = int(request.args.get('page'))
        pgcount = len(all_news)
        class npgstore:
            value = pgcount
        if curr_page > pgcount:
            abort(404)
        match curr_page:
            case 0:
                n = all_news[0]
                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
            case npgstore.value:
                n = all_news[pgcount]
                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
            case _:
                n = all_news[curr_page]
                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
        return render_template('news.html', user = user, page = curr_page, pagecount = pgcount, news = n, time = presentTime2, cati = spis_cati, is_sort = is_sort)

@app.route('/news/addnews/', methods=['POST', 'GET'])
def add_news():
    if 'login' in session:
        if request.method == 'POST':
            new_n = News(maintext = request.form.get("new_news"), category = request.form.get("category"), user_id = Users.query.filter_by(email = session['login']).first().id)
            dbalc.session.add(new_n)
            dbalc.session.commit()

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

@app.route('/editnews/', methods=['POST', 'GET'])
def edit_news():
    if request.args.get('del'):
        nn = int(request.args.get('news'))
        x = News.query.filter_by(id=nn).first()
        user = Users.query.filter_by(id = x.user_id).first()
        dbalc.session.delete(x)
        dbalc.session.commit()
        return redirect(url_for('account') + '?user=' + user.email)
    if 'login' in session:
        nnn = request.args.get('news')
        if not nnn:
            abort(404)
        news = News.query.filter_by(id=request.args.get('news')).first()
        u = Users.query.filter_by(email=session['login']).first()
        if u.id != news.user_id and u.role != 'Админ':
            abort(404)
        if request.method == 'POST':
            ed_news = News.query.filter_by(id = nnn).first()
            ed_news.maintext = request.form.get('edit_news')
            ed_news.category = request.form.get('category')
            dbalc.session.commit()
        cati = Categories.query.all()
        user = Users.query.filter_by(id = news.user_id).first()
        spis_cati = []
        for i in range(len(cati)):
            spis_cati.append(cati[i].category)
        return render_template('editnews.html', news = news, cati = spis_cati, user = user)
    else:
        abort(404)

@app.route('/news/newsbycat/', methods=['POST', 'GET'])
def by_cat():
    all_news = []
    cata = ""
    if not request.args.get('page') or not request.args.get('cata'):
        abort(404)
    if 'login' not in session:
        flash("Авторизируйтесь, чтобы просматривать и добавлять новости")
        return redirect(url_for('auth'))
    else:
        cati = Categories.query.all()
        spis_cati = []
        cata = request.args.get('cata')
        for i in range(len(cati)):
            spis_cati.append(cati[i].category)
        if request.method == 'POST':
            all_news = News.query.filter_by(category = request.form.get('category_sort')).order_by(News.date_created.desc()).all()
            cata = request.form.get('category_sort')
        else:
            all_news = News.query.filter_by(category=request.args.get('cata')).order_by(News.date_created.desc()).all()
        if all_news == []:
            flash("Станьте первым, кто выложит новость")
            return render_template('newsbycat.html', all_news = all_news, cati = spis_cati)
        user = Users.query.filter_by(id=all_news[0].user_id).first()
        curr_page = int(request.args.get('page'))
        pgcount = len(all_news)
        class npgstore:
            value = pgcount
        if curr_page > pgcount:
            abort(404)
        match curr_page:
            case 0:
                n = all_news[0]

                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
            case npgstore.value:
                n = all_news[pgcount]
                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
            case _:
                n = all_news[curr_page]
                user = Users.query.filter_by(id=n.user_id).first()
                presentTime = n.date_created
                presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
        return render_template('newsbycat.html', user=user, page=curr_page, pagecount=pgcount, news=n, time=presentTime2, cati=spis_cati, cata = cata)

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
