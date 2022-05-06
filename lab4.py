from datetime import datetime
from time import sleep

from flask import Flask, url_for, render_template, request, send_from_directory, g, abort, flash, session
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_session import Session
from werkzeug.utils import redirect, secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import loginform
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from threading import Thread

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import vk_api


vk_session = vk_api.VkApi(token="8a8c105055d8984df26032fc1a4721012a2c37560d89e736b0b62f884486f636e131da76d4f3019e59f24")
session_api = vk_session.get_api()
longpool = VkLongPoll(vk_session)

keyboard = VkKeyboard()
keyboard.add_button("Привет", VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button("Хочу получать новости", VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button("Я не хочу получать новости", VkKeyboardColor.NEGATIVE)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'flsite.db'
DEBUG = False
SECRET_KEY = '&8\xa2|\x11\x0f\xcf\xe8\xc2\xa6\x85"\xfd~\x0c#\x06{>T\xb7\xe9\xd8\xc9'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
app.config['SESSION_PEMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///maindb.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
login_manager = LoginManager(app)
dbalc = SQLAlchemy(app)


last_cata = ""

followers = dbalc.Table('followers',
    dbalc.Column('follower_id', dbalc.Integer, dbalc.ForeignKey('users.id')),
    dbalc.Column('followed_id', dbalc.Integer, dbalc.ForeignKey('users.id'))
)

class Users(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key = True, autoincrement=True)
    name = dbalc.Column(dbalc.String(50), nullable = False)
    surname = dbalc.Column(dbalc.String(50), nullable=False)
    email = dbalc.Column(dbalc.String(50), unique = False)
    age = dbalc.Column(dbalc.Integer, nullable = False)
    work = dbalc.Column(dbalc.String(50), nullable = False)
    post = dbalc.Column(dbalc.String(50), nullable=False)
    password = dbalc.Column(dbalc.String(500), nullable = False)
    photo = dbalc.Column(dbalc.String(500), nullable=False)
    role = dbalc.Column(dbalc.String(50), nullable=False)
    followed = dbalc.relationship('Users',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=dbalc.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def get_followers(self):
        return self.followed.filter(followers.c.followed_id == self.id)
class News(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key=True, autoincrement=True)
    maintext = dbalc.Column(dbalc.String(5000), nullable=False)
    category = dbalc.Column(dbalc.String(100))
    date_created = dbalc.Column(dbalc.DateTime, default=datetime.utcnow())
    user_id = dbalc.Column(dbalc.Integer)

class Categories(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key=True, autoincrement=True)
    category = dbalc.Column(dbalc.String(100), nullable=True)

class Bot(dbalc.Model):
    id = dbalc.Column(dbalc.Integer, primary_key = True, autoincrement=True)
    id_vk = dbalc.Column(dbalc.String(100), nullable = True)

def sender(id, text, keyboard):
    vk_session.method('messages.send', {
        'user_id': id,
        'message': text,
        'random_id': 0,
        'keyboard': keyboard.get_keyboard()
    })

def send_msg(text):
    all_users = Bot.query.all()
    for i in all_users:
        sender(i.id_vk, 'Вышла новая запись от пользователя ' + text + '. Вы можете посмотреть ее на сайте http://egorhramkov.pythonanywhere.com/mainpage/',keyboard)

def aaa():
    for event in longpool.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                msg = event.text.lower()
                id = event.user_id

                if msg == 'начать':
                    sender(id, 'Привет', keyboard)

                if msg == 'привет':
                    sender(id, 'и тебе привет', keyboard)

                if msg == 'хочу получать новости':
                    if not Bot.query.filter_by(id_vk = id).first():
                        u = Bot(id_vk = id)
                        dbalc.session.add(u)
                        #dbalc.session.flush()
                        dbalc.session.commit()
                        sender(id, 'Теперь вы подписаны на рассылку!', keyboard)
                    else:
                        sender(id, 'Вы уже подписаны на рассылку!', keyboard)

                if msg == 'я не хочу получать новости':
                    u = Bot.query.filter_by(id_vk = id).first()
                    if(Bot.query.filter_by(id_vk = id).first()):
                        dbalc.session.delete(u)
                        dbalc.session.commit()
                        sender(id, 'Вы отписались от рассылки', keyboard)
                    else:
                        sender(id, 'Но вы итак не подписаны на рассылку', keyboard)

new_thread = Thread(target=aaa)
new_thread.start()

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
                if Users.query.filter_by(email = request.form.get('email')).first():
                    flash("Такой пользователь уже зарегистрирован!")
                    return redirect(url_for('register'))
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
            u1 = Users.query.filter_by(email = session['login']).first()
            if u1.is_following(user):
                is_flw = True
            else:
                is_flw = False
            return render_template('account.html', user=user, id_sess=session['login'], is_adm=is_adm, news_of_user = news_of_user, is_flw = is_flw)
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
            send_msg(Users.query.filter_by(email=session['login']).first().name + ' ' + Users.query.filter_by(email=session['login']).first().surname)

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

@app.route('/follow/', methods=['POST', 'GET'])
def follow():
    if request.method == 'GET':
        obj = request.args.get('email')
        action = request.args.get('action')
        if action == 'subscribe':
            print("ЗАШЛО")
            user = Users.query.filter_by(email=session['login']).first()
            user2 = Users.query.filter_by(email=obj).first()
            u = user.follow(user2)
            dbalc.session.add(u)
            dbalc.session.commit()
        elif action == 'unsubscribe':
            user = Users.query.filter_by(email=session['login']).first()
            user2 = Users.query.filter_by(email=obj).first()
            u = user.unfollow(user2)
            assert u != None
            dbalc.session.add(u)
            dbalc.session.commit()
    return redirect(url_for('account')+'?user=' + user2.email)

@app.route('/followers/')
def list_followers():
    flw = request.args.get('flw')
    user = Users.query.filter_by(email=session['login']).first()
    if flw == 'subs':
        title = 'Подписки'
        list_subs = user.followed.all()
        if list_subs == []:
            flash('У вас нет подписок')
    if flw == 'subd':
        title = 'Подписчики'
        list_subs = user.followers.all()
        if list_subs == []:
            flash('У вас нет подписчиков')

    return render_template('followers.html', lists = list_subs, title=title)


@app.route('/newsbysub/')
def newsbysub():
    spis_all_news = []
    temp_all_news = []
    if not request.args.get('page'):
        abort(404)
    if 'login' not in session:
        flash("Авторизируйтесь, чтобы просматривать и добавлять новости")
        return redirect(url_for('auth'))
    else:
        user = Users.query.filter_by(email=session['login']).first()
        list_subs = list(user.followed.all())
        if list_subs == []:
            flash("Подпишитесь на кого-нибудь, чтобы следить за его новостями!")
            return render_template('newsbysub.html', all_news = list_subs)
        for i in list_subs:
            iter = 0
            temp_all_news = []
            temp_all_news.append(News.query.filter_by(user_id=i.id).all())
            if temp_all_news != []:
                for news in temp_all_news[iter]:
                    spis_all_news.append(news)
                    iter += 1
        spis_all_news = sorted(spis_all_news, key=lambda x: x.date_created)[::-1]
        if spis_all_news == []:
            flash("Тут пока что ничего нет :(")
            return render_template('newsbysub.html', all_news = spis_all_news)

        curr_page = int(request.args.get('page'))
        pgcount = len(spis_all_news)
        remainder = 0

        class npgstore:
            value = pgcount

        if curr_page == 0:
            n = spis_all_news[0]
            user = Users.query.filter_by(id=n.user_id).first()
            presentTime = n.date_created
            presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
        if curr_page == npgstore.value:
            n = spis_all_news[pgcount]
            user = Users.query.filter_by(id=n.user_id).first()
            presentTime = n.date_created
            presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')
        if curr_page != npgstore.value and curr_page != 0:
            n = spis_all_news[curr_page]
            user = Users.query.filter_by(id=n.user_id).first()
            presentTime = n.date_created
            presentTime2 = presentTime.strftime('%B %d %Y - %H:%M:%S')


    return render_template('newsbysub.html', news = n, time = presentTime2, user = user, pagecount = pgcount)

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')

