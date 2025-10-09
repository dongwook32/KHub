import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'a-very-secret-and-long-random-string-for-security' 

# --- 데이터베이스 설정 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 데이터베이스 모델(테이블) 정의 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- 로그인 확인 '문지기' 함수 (데코레이터) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("로그인이 필요한 서비스입니다.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 라우트(페이지) 정의 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # ... (이전과 동일한 회원가입 로직) ...
    if request.method == 'POST':
        # ... form data ...
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        name = request.form.get('name')
        gender = request.form.get('gender')
        birthday_str = request.form.get('birthday')
        status = request.form.get('status')

        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('register'))
        if User.query.filter_by(student_id=student_id).first():
            flash('이미 가입된 학번입니다.')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        birthday_obj = datetime.strptime(birthday_str, '%Y-%m-%d').date()
        
        new_user = User(
            student_id=student_id, email=email, password=hashed_password,
            name=name, gender=gender, birthday=birthday_obj, status=status
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        flash(f"{new_user.name}님, 가입을 환영합니다!")
        return redirect(url_for('mypage'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('studentId')
        password = request.form.get('password')
        user = User.query.filter_by(student_id=student_id).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash(f"{user.name}님, 환영합니다!")
            return redirect(url_for('mypage'))
        flash("아이디(학번) 또는 비밀번호를 확인하세요.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("성공적으로 로그아웃되었습니다.")
    return redirect(url_for('index'))

@app.route('/boards')
@login_required
def boards():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('boards.html', posts=posts)

@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        user_id = session['user_id']
        if not title or not content:
            flash("제목과 내용을 모두 입력해주세요.")
            return render_template('create_post.html')
        new_post = Post(title=title, content=content, user_id=user_id)
        db.session.add(new_post)
        db.session.commit()
        flash("새 글이 성공적으로 등록되었습니다.")
        return redirect(url_for('boards'))
    return render_template('create_post.html')

# --- 여기를 수정했습니다 ---
@app.route('/mypage')
@login_required
def mypage():
    # 세션에 저장된 user_id를 이용해 데이터베이스에서 현재 사용자 정보를 찾습니다.
    user_id = session.get('user_id')
    # .get()을 사용하면 혹시 모를 오류를 방지할 수 있습니다.
    user = User.query.get(user_id) if user_id else None
    
    # 사용자 정보가 없으면 홈페이지로 보냅니다.
    if user is None:
        flash("사용자 정보를 찾을 수 없습니다. 다시 로그인해주세요.")
        return redirect(url_for('login'))

    # 찾은 사용자 정보를 'user'라는 변수 이름으로 mypage.html에 전달합니다.
    return render_template('mypage.html', user=user)
# -------------------------

@app.route('/chat')
@login_required
def chat():
    if 'anon_profile' not in session:
        return redirect(url_for('profile_setup'))
    anon_profile = session.get('anon_profile', {})
    return render_template('chat.html', anon_profile=anon_profile)

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        session['anon_profile'] = {
            'year': request.form.get('year'), 'gender': request.form.get('gender'),
            'nickname': request.form.get('nickname', '익명의친구'),
            'bio': request.form.get('bio', ''), 'interests': request.form.getlist('interests')
        }
        return redirect(url_for('chat'))
    return render_template('profile-setup.html')

