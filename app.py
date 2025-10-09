import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ❗ 중요: 'change-me' 부분은 아무도 모르는 복잡한 문자열로 꼭 바꾸세요!
app.secret_key = 'change-me' 

# --- 데이터베이스 설정 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ----------------------

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
# ---------------------------------

# --- 로그인 확인 '문지기' 함수 (데코레이터) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("로그인이 필요한 서비스입니다.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
# ----------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
            student_id=student_id, 
            email=email, 
            password=hashed_password,
            name=name,
            gender=gender,
            birthday=birthday_obj,
            status=status
        )
        
        db.session.add(new_user)
        db.session.commit()

        # --- 여기부터 변경된 부분 ---
        # 세션에 새로 가입한 사용자의 id를 저장하여 바로 로그인 처리
        session['user_id'] = new_user.id
        
        flash(f"{new_user.name}님, 가입을 환영합니다!")
        return redirect(url_for('mypage')) # 마이페이지로 이동
        # -------------------------
    
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId')
    password = request.form.get('password')

    user = User.query.filter_by(student_id=student_id).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        flash(f"{user.name}님, 환영합니다!")
        return redirect(url_for('mypage'))
        
    flash("아이디(학번) 또는 비밀번호를 확인하세요.")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("성공적으로 로그아웃되었습니다.")
    return redirect(url_for('index'))

@app.route('/mypage')
@login_required
def mypage():
    return render_template('mypage.html')

@app.route('/chat')
@login_required
def chat():
    if 'anon_profile' not in session:
        return redirect(url_for('profile_setup'))
    anon_profile = session.get('anon_profile', {})
    return render_template('chat.html', anon_profile=anon_profile)

@app.route('/boards')
@login_required
def boards():
    return render_template('boards.html')

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        session['anon_profile'] = {
            'year': request.form.get('year'),
            'gender': request.form.get('gender'),
            'nickname': request.form.get('nickname', '익명의친구'),
            'bio': request.form.get('bio', ''),
            'interests': request.form.getlist('interests')
        }
        return redirect(url_for('chat'))
    
    return render_template('profile-setup.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)