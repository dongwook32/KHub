import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ❗ 중요: 'change-me' 부분은 아무도 모르는 복잡한 문자열로 꼭 바꾸세요!
app.secret_key = 'change-me' 

# --- 데이터베이스 설정 ---
# Render 환경 변수에 설정된 데이터베이스 URL을 가져옵니다.
# 로컬 테스트 시에는 이 환경 변수가 없으므로 기본 SQLite DB를 사용하도록 설정할 수 있습니다.
# 하지만 지금은 Render 배포가 목표이므로 os.environ.get('DATABASE_URL')만 사용합니다.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ----------------------

# --- 데이터베이스 모델(테이블) 정의 ---
# 'User'라는 이름의 테이블을 설계합니다.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 고유 번호
    student_id = db.Column(db.String(80), unique=True, nullable=False) # 학번 (고유값)
    password = db.Column(db.String(200), nullable=False) # 비밀번호 (실제로는 암호화해서 저장해야 함)

# 여기에 Post, Comment 등 필요한 다른 테이블 모델도 추가할 수 있습니다.
# ---------------------------------

# --- 로그인 확인 '문지기' 함수 (데코레이터) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # 세션에 user_id 정보가 없으면
            flash("로그인이 필요한 서비스입니다.") # 메시지를 준비하고
            return redirect(url_for('login')) # 로그인 페이지로 보냅니다.
        return f(*args, **kwargs)
    return decorated_function
# ----------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId')
    pw = request.form.get('password')

    # 데이터베이스에서 해당 학번의 사용자를 찾습니다.
    user = User.query.filter_by(student_id=student_id).first()

    # 사용자가 존재하고 비밀번호가 맞다면 (실제로는 암호화된 비밀번호를 비교해야 함)
    if user and user.password == pw:
        session['user_id'] = user.id # 세션에는 이제 데이터베이스의 고유 id를 저장합니다.
        flash(f"{user.student_id}님, 환영합니다!")
        return redirect(url_for('mypage'))
        
    flash("아이디(학번) 또는 비밀번호를 확인하세요.")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear() # 세션의 모든 정보를 삭제합니다.
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
    # 앞으로 이곳에서 DB에 저장된 게시글들을 불러오는 코드를 추가하게 됩니다.
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

# 이 코드는 로컬에서 테스트할 때만 실행됩니다.
if __name__ == '__main__':
    # 앱 컨텍스트 내에서 데이터베이스 테이블을 생성합니다.
    # 이미 테이블이 존재하면 아무 작업도 하지 않습니다.
    with app.app_context():
        db.create_all()
    app.run(debug=True)