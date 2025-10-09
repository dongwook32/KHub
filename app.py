from flask import Flask, render_template, request, redirect, url_for, session, flash # <-- flash 추가
from functools import wraps # <-- wraps 추가

app = Flask(__name__)
# ❗ 중요: 'change-me' 부분은 아무도 모르는 복잡한 문자열로 꼭 바꾸세요!
app.secret_key = 'change-me' 

# --- 로그인 확인 '문지기' 함수 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session: # 세션에 'user' 정보가 없으면
            flash("로그인이 필요한 서비스입니다.") # 메시지를 준비하고
            return redirect(url_for('login')) # 로그인 페이지로 보냅니다.
        return f(*args, **kwargs)
    return decorated_function
# ---------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    pw = request.form.get('password')
    # 실제로는 여기서 DB와 비교해야 하지만, 지금은 간단히 처리
    if email and pw:
        session['user'] = email
        return redirect(url_for('mypage'))
    flash("이메일 또는 비밀번호를 확인하세요.")
    return redirect(url_for('login'))

# --- 로그아웃 기능 추가 ---
@app.route('/logout')
def logout():
    session.clear() # 세션의 모든 정보를 삭제합니다.
    flash("로그아웃되었습니다.")
    return redirect(url_for('index'))
# --------------------------

@app.route('/mypage')
@login_required # <-- 문지기 적용!
def mypage():
    return render_template('mypage.html')

@app.route('/chat')
@login_required # <-- 문지기 적용!
def chat():
    # 익명 프로필이 없으면 프로필 설정 페이지로 리디렉트
    if 'anon_profile' not in session:
        return redirect(url_for('profile_setup'))
    
    # 세션에서 익명 프로필 가져오기
    anon_profile = session.get('anon_profile', {})
    return render_template('chat.html', anon_profile=anon_profile)

@app.route('/boards')
@login_required # <-- 문지기 적용!
def boards():
    return render_template('boards.html')

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required # <-- 문지기 적용!
def profile_setup():
    if request.method == 'POST':
        # 프로필 데이터 수집
        year = request.form.get('year')
        gender = request.form.get('gender')
        nickname = request.form.get('nickname', '익명의친구')
        bio = request.form.get('bio', '')
        interests = request.form.getlist('interests')
        
        # 세션에 익명 프로필 저장
        session['anon_profile'] = {
            'year': year,
            'gender': gender,
            'nickname': nickname,
            'bio': bio,
            'interests': interests
        }
        
        # 채팅 페이지로 리디렉트
        return redirect(url_for('chat'))
    
    return render_template('profile-setup.html')

if __name__ == '__main__':
    app.run(debug=True)