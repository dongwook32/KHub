import os
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
    id = db.Column(db.Integer, primary_key=True) # 고유 번호
    student_id = db.Column(db.String(80), unique=True, nullable=False) # 학번 (고유값)
    password = db.Column(db.String(200), nullable=False) # 암호화된 비밀번호
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        student_id = request.form.get('studentId')
        password = request.form.get('password')

        if not student_id or not password:
            flash('학번과 비밀번호를 모두 입력해주세요.')
            return redirect(url_for('signup'))

        user = User.query.filter_by(student_id=student_id).first()
        if user:
            flash('이미 가입된 학번입니다.')
            return redirect(url_for('signup'))

        # 비밀번호를 암호화(해싱)해서 저장
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(student_id=student_id, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('signup.html') # GET 요청 시 회원가입 페이지 보여주기

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId')
    password = request.form.get('password')

    user = User.query.filter_by(student_id=student_id).first()

    # 암호화된 비밀번호를 확인
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        flash(f"{user.student_id}님, 환영합니다!")
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