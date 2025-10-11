from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'change-me'

# 데이터 저장 파일 경로
DATA_FILE = 'registered_users.json'

def load_users():
    """등록된 사용자 정보 불러오기"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users):
    """등록된 사용자 정보 저장하기"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def is_student_id_duplicate(student_id):
    """학번 중복 체크"""
    users = load_users()
    return any(user.get('student_id') == student_id for user in users)

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
        
        # 학번 중복 체크
        if is_student_id_duplicate(student_id):
            flash('이미 존재하는 학번입니다. 다른 학번으로 회원가입해주세요.', 'error')
            return redirect(url_for('register'))
        
        # 사용자 정보 저장
        users = load_users()
        new_user = {
            'name': name,
            'student_id': student_id,
            'birthday': birthday,
            'gender': gender,
            'status': status,
            'email': email,
            'password': password  # 실제로는 해시화해야 함
        }
        users.append(new_user)
        
        if not save_users(users):
            flash('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
            return redirect(url_for('register'))
        
        # 회원가입 성공 - 세션에 저장하지 않음 (로그인 필요)
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        # 로그인 페이지로 리디렉트
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    student_id = request.form.get('studentId', '').strip()
    pw = request.form.get('password', '').strip()
    
    if student_id and pw:
        # 등록된 사용자 확인
        users = load_users()
        user = next((u for u in users if u.get('student_id') == student_id), None)
        
        if user:
            # 비밀번호 확인 (실제로는 해시 비교해야 함)
            if user.get('password') == pw:
                # 학번에서 학과 코드 추출 (5~6번째 자리)
                # 학번 형식: YYYY(입학년도 4자리) + 학과코드(2자리) + 번호(3자리) = 9자리
                if len(student_id) >= 6:
                    dept_code = student_id[4:6]
                    
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
                        'name': user.get('name'),
                        'student_id': student_id,
                        'birthday': user.get('birthday'),
                        'gender': user.get('gender'),
                        'status': user.get('status'),
                        'email': user.get('email'),
                        'department': department,
                        'dept_code': dept_code
                    }
                else:
                    session['user'] = {
                        'name': user.get('name'),
                        'student_id': student_id,
                        'birthday': user.get('birthday'),
                        'gender': user.get('gender'),
                        'status': user.get('status'),
                        'email': user.get('email'),
                        'department': 'free',
                        'dept_code': 'unknown'
                    }
                
                flash('로그인되었습니다!', 'success')
                return redirect(url_for('mypage'))
            else:
                flash('비밀번호가 올바르지 않습니다.', 'error')
                return redirect(url_for('login'))
        else:
            # 등록되지 않은 사용자
            flash('등록되지 않은 학번입니다. 회원가입을 먼저 진행해주세요.', 'error')
            return redirect(url_for('login'))
    
    flash('학번과 비밀번호를 입력해주세요.', 'error')
    return redirect(url_for('login'))

@app.route('/mypage')
def mypage():
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    return render_template('mypage.html')

@app.route('/chat')
def chat():
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    # 익명 프로필이 없으면 프로필 설정 페이지로 리디렉트
    if 'anon_profile' not in session:
        return redirect(url_for('profile_setup'))
    
    # 세션에서 익명 프로필 가져오기
    anon_profile = session.get('anon_profile', {})
    return render_template('chat.html', anon_profile=anon_profile)

@app.route('/boards')
def boards():
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    # 세션에서 사용자 정보 가져오기
    user = session.get('user', {})
    user_department = user.get('department', 'free') if isinstance(user, dict) else 'free'
    
    return render_template('boards.html', user_department=user_department)

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/api/check-student-id', methods=['POST'])
def check_student_id():
    """학번 중복 체크 API"""
    data = request.get_json()
    student_id = data.get('student_id', '')
    
    if not student_id:
        return jsonify({'error': '학번을 입력해주세요.'}), 400
    
    is_duplicate = is_student_id_duplicate(student_id)
    return jsonify({
        'duplicate': is_duplicate,
        'message': '이미 존재하는 학번입니다.' if is_duplicate else '사용 가능한 학번입니다.'
    })

@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/change-password', methods=['POST'])
def change_password():
    """비밀번호 변경"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 요청 데이터 가져오기
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': '모든 필드를 입력해주세요.'}), 400
    
    # 사용자 데이터 로드
    users = load_users()
    user = next((u for u in users if u.get('student_id') == student_id), None)
    
    if not user:
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'}), 404
    
    # 현재 비밀번호 확인
    if user.get('password') != current_password:
        return jsonify({'success': False, 'message': '현재 비밀번호가 올바르지 않습니다.'}), 400
    
    # 비밀번호 업데이트
    user['password'] = new_password
    
    # 변경된 사용자 목록 저장
    if not save_users(users):
        return jsonify({'success': False, 'message': '비밀번호 변경 중 오류가 발생했습니다.'}), 500
    
    return jsonify({
        'success': True, 
        'message': '비밀번호가 성공적으로 변경되었습니다.'
    })

@app.route('/delete-account', methods=['POST'])
def delete_account():
    """회원 탈퇴"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 사용자 데이터 로드
    users = load_users()
    
    # 해당 사용자 찾아서 삭제
    original_count = len(users)
    users = [user for user in users if user.get('student_id') != student_id]
    
    if len(users) == original_count:
        # 사용자를 찾지 못한 경우 (등록되지 않은 사용자일 수 있음)
        session.clear()
        return jsonify({
            'success': True, 
            'message': '회원 탈퇴가 완료되었습니다.',
            'redirect': url_for('index')
        })
    
    # 변경된 사용자 목록 저장
    if not save_users(users):
        return jsonify({'success': False, 'message': '회원 탈퇴 중 오류가 발생했습니다.'}), 500
    
    # 세션 삭제
    session.clear()
    
    return jsonify({
        'success': True, 
        'message': '회원 탈퇴가 완료되었습니다. 그동안 이용해주셔서 감사합니다.',
        'redirect': url_for('index')
    })

@app.route('/profile-setup', methods=['GET', 'POST'])
def profile_setup():
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
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
