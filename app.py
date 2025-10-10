from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'change-me'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 회원가입 데이터 수집
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        birthday = request.form.get('birthday')
        gender = request.form.get('gender')
        status = request.form.get('status')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 여기서 실제로는 DB에 저장해야 함
        # 시연용으로 세션에 저장
        session['user'] = {
            'name': name,
            'student_id': student_id,
            'birthday': birthday,
            'gender': gender,
            'status': status,
            'email': email
        }
        
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        # 로그인 페이지로 리디렉트
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId')
    pw = request.form.get('password')
    
    if student_id and pw:
        # 학번에서 학과 코드 추출 (3~4번째 자리)
        if len(student_id) >= 4:
            dept_code = student_id[2:4]
            
            # 학과 코드에 따른 학과 매핑
            dept_mapping = {
                '01': 'bible',      # 성서학과
                '02': 'social',     # 사회복지학과
                '03': 'child',      # 영유아보육학과
                '04': 'ai',         # 컴퓨터소프트웨어학과/AI융합학부
                '05': 'nursing',    # 간호학과
                '06': 'ai'          # AI융합학부 (04와 같은 그룹)
            }
            
            department = dept_mapping.get(dept_code, 'free')
            
            # 세션에 사용자 정보 저장
            session['user'] = {
                'student_id': student_id,
                'department': department,
                'dept_code': dept_code
            }
        else:
            session['user'] = {
                'student_id': student_id,
                'department': 'free',
                'dept_code': 'unknown'
            }
        
        return redirect(url_for('mypage'))
    return redirect(url_for('login'))

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

@app.route('/chat')
def chat():
    # 익명 프로필이 없으면 프로필 설정 페이지로 리디렉트
    if 'anon_profile' not in session:
        return redirect(url_for('profile_setup'))
    
    # 세션에서 익명 프로필 가져오기
    anon_profile = session.get('anon_profile', {})
    return render_template('chat.html', anon_profile=anon_profile)

@app.route('/boards')
def boards():
    # 세션에서 사용자 정보 가져오기
    user = session.get('user', {})
    user_department = user.get('department', 'free') if isinstance(user, dict) else 'free'
    
    return render_template('boards.html', user_department=user_department)

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/profile-setup', methods=['GET', 'POST'])
def profile_setup():
    if request.method == 'POST':
        # 프로필 데이터 수집
        year = request.form.get('year')
        gender = request.form.get('gender')
        nickname = request.form.get('nickname', '익명의친구')
        bio = request.form.get('bio', '')
        interests = request.form.getlist('interests')
        
        # 필수 필드 검증
        if not year or not gender or not interests:
            flash('모든 필수 항목을 입력해주세요.', 'error')
            return redirect(url_for('profile_setup'))
        
        # 세션에 익명 프로필 저장
        session['anon_profile'] = {
            'year': year,
            'gender': gender,
            'nickname': nickname,
            'bio': bio,
            'interests': interests
        }
        
        flash('익명 프로필이 저장되었습니다!', 'success')
        # 채팅 페이지로 리디렉트
        return redirect(url_for('chat'))
    
    return render_template('profile-setup.html')

if __name__ == '__main__':
    app.run(debug=True)
