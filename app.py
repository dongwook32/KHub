from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'change-me' # ❗ 실제 서비스 시에는 더 복잡한 키로 변경하세요.

# --- 로그인 확인 '문지기' 함수 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # <-- session['user_id']를 확인하도록 변경
            flash("로그인이 필요한 서비스입니다.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId') # <-- name="studentId" 값을 받도록 변경
    pw = request.form.get('password')
    
    # 실제 DB 검증 로직이 필요하지만, 현재는 간단히 처리
    if student_id and pw:
        session['user_id'] = student_id # <-- session['user_id']로 저장
        return redirect(url_for('mypage'))
        
    flash("아이디(학번) 또는 비밀번호를 확인하세요.")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("로그아웃되었습니다.")
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
    app.run(debug=True)