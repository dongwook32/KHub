import os
from datetime import datetime # 날짜 처리를 위해 추가
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'change-me' # ❗ 실제 서비스 시에는 더 복잡한 키로 변경하세요.

# --- 데이터베이스 설정 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ----------------------

# --- 데이터베이스 모델(테이블) 정의 (확장됨) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # 이메일 추가
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(80), nullable=False) # 이름 추가
    gender = db.Column(db.String(10), nullable=False) # 성별 추가
    birthday = db.Column(db.Date, nullable=False) # 생년월일 추가
    status = db.Column(db.String(20), nullable=False) # 재학 상태 추가
# ---------------------------------------------

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

# --- 회원가입 라우트 (이름 변경 및 로직 확장) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # form에서 모든 데이터 가져오기
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        name = request.form.get('name')
        gender = request.form.get('gender')
        birthday_str = request.form.get('birthday')
        status = request.form.get('status')

        # 서버 측 유효성 검사
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('register'))

        if User.query.filter_by(student_id=student_id).first():
            flash('이미 가입된 학번입니다.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.')
            return redirect(url_for('register'))

        # 비밀번호 암호화
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # 생년월일 문자열을 날짜 객체로 변환
        birthday_obj = datetime.strptime(birthday_str, '%Y-%m-%d').date()
        
        # 모든 정보를 담아 새 사용자 생성
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

        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    # GET 요청 시에는 회원가입 페이지를 보여줌
    return render_template('register.html')
# -------------------------------------------

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId') # 로그인 폼의 name은 studentId
    password = request.form.get('password')

    user = User.query.filter_by(student_id=student_id).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        flash(f"{user.name}님, 환영합니다!") # 이제 이름으로 환영 메시지를 보냅니다.
        return redirect(url_for('mypage'))
        
    flash("아이디(학번) 또는 비밀번호를 확인하세요.")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("성공적으로 로그아웃되었습니다.")
    return redirect(url_for('index'))

# --- 나머지 라우트들은 이전과 동일 ---
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