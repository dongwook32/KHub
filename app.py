import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ❗ 중요: 'change-me' 부분은 실제 서비스 시 아무도 모르는 복잡한 문자열로 꼭 바꾸세요!
app.secret_key = 'a-very-secret-and-complex-key-change-it' 

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
    nickname = db.Column(db.String(80), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")

        # User와 AnonProfile을 1대1 관계로 연결
    anon_profile = db.relationship('AnonProfile', backref='user', uselist=False, cascade="all, delete-orphan")

# [추가] 익명 프로필 테이블 모델
class AnonProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True) # JSON 문자열로 저장
    # User 테이블과 연결하는 외래 키
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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

# --- 🔑 임시: DB 테이블 생성을 위한 비밀 주소 ---
@app.route('/init-db-super-secret-key-12345')
def init_db():
    with app.app_context():
        db.create_all()
    return "데이터베이스 테이블이 최신 상태로 업데이트 되었습니다!"
# ----------------------------------------------------

# --- 메인 라우트 ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 인증 관련 라우트 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # (이전과 동일한 회원가입 로직)
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        name = request.form.get('name')
        gender = request.form.get('gender')
        birthday_str = request.form.get('birthday')
        status = request.form.get('status')

        if not all([student_id, email, password, password_confirm, name, gender, birthday_str, status]):
            flash('모든 필수 항목을 입력해주세요.')
            return redirect(url_for('register'))

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

# --- 마이페이지 및 프로필 관련 라우트 ---
@app.route('/mypage')
@login_required
def mypage():
    user = User.query.get_or_404(session['user_id'])
    # mypage.html에 user 정보와 함께 anon_profile 정보도 전달
    return render_template('mypage.html', user=user, anon_profile=user.anon_profile)

# [추가] 익명 프로필 저장/수정 라우트
@app.route('/save-anon-profile', methods=['POST'])
@login_required
def save_anon_profile():
    user = User.query.get(session['user_id'])
    
    nickname = request.form.get('nickname')
    year = request.form.get('year')
    gender = request.form.get('gender')
    bio = request.form.get('bio')
    interests = request.form.getlist('interests') # 리스트로 받음

    # 서버 측 유효성 검사
    if not all([nickname, year, gender, interests]):
        flash('닉네임, 학번, 성별, 관심사는 필수 항목입니다.')
        return redirect(url_for('mypage'))

    # [수정] 서버에서 직접 닉네임 중복 검사
    existing_profile = AnonProfile.query.filter_by(nickname=nickname).first()
    if existing_profile and existing_profile.user_id != user.id:
        flash('이미 사용 중인 익명 닉네임입니다.')
        return redirect(url_for('mypage'))

    # 기존 프로필이 있으면 업데이트, 없으면 새로 생성
    anon_profile = user.anon_profile
    if not anon_profile:
        anon_profile = AnonProfile(user_id=user.id)
    
    anon_profile.nickname = nickname
    anon_profile.year = year
    anon_profile.gender = gender
    anon_profile.bio = bio
    anon_profile.interests = json.dumps(interests) # 리스트를 JSON 문자열로 변환하여 저장
    
    db.session.add(anon_profile)
    db.session.commit()
    
    flash('익명카드가 성공적으로 저장되었습니다.')
    return redirect(url_for('mypage'))

@app.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    user.nickname = request.form.get('nickname')
    user.bio = request.form.get('bio')
    db.session.commit()
    flash('프로필이 성공적으로 수정되었습니다.')
    return redirect(url_for('mypage'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(user.password, current_password):
        flash('현재 비밀번호가 일치하지 않습니다.')
        return redirect(url_for('mypage'))
    
    if new_password != confirm_password:
        flash('새 비밀번호가 일치하지 않습니다.')
        return redirect(url_for('mypage'))
    
    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    flash('비밀번호가 성공적으로 변경되었습니다.')
    return redirect(url_for('mypage'))

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('회원 탈퇴가 완료되었습니다.')
    return redirect(url_for('index'))

# --- 게시판 관련 라우트 ---
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

# --- 기타 페이지 라우트 ---
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
            'year': request.form.get('year'),
            'gender': request.form.get('gender'),
            'nickname': request.form.get('nickname', '익명의친구'),
            'bio': request.form.get('bio', ''),
            'interests': request.form.getlist('interests')
        }
        return redirect(url_for('chat'))
    return render_template('profile-setup.html')

# 로컬에서 테스트할 때만 실행됩니다.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

