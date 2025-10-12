from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'change-me'

# 데이터 저장 파일 경로
DATA_FILE = 'registered_users.json'
ANON_PROFILES_FILE = 'anon_profiles.json'
BOARD_POSTS_FILE = 'board_posts.json'
BOARD_COMMENTS_FILE = 'board_comments.json'
CHAT_MESSAGES_FILE = 'chat_messages.json'

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
        print(f"[데이터 저장 성공] {len(users)}명의 사용자 정보 저장됨")
        return True
    except Exception as e:
        print(f"[데이터 저장 실패] 오류: {e}")
        return False

def is_student_id_duplicate(student_id):
    """학번 중복 체크"""
    users = load_users()
    return any(user.get('student_id') == student_id for user in users)

def load_anon_profiles():
    """익명 프로필 불러오기"""
    if os.path.exists(ANON_PROFILES_FILE):
        try:
            with open(ANON_PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_anon_profiles(profiles):
    """익명 프로필 저장하기"""
    try:
        with open(ANON_PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_board_posts():
    """게시글 불러오기"""
    if os.path.exists(BOARD_POSTS_FILE):
        try:
            with open(BOARD_POSTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_board_posts(posts):
    """게시글 저장하기"""
    try:
        with open(BOARD_POSTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_board_comments():
    """댓글 불러오기"""
    if os.path.exists(BOARD_COMMENTS_FILE):
        try:
            with open(BOARD_COMMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_board_comments(comments):
    """댓글 저장하기"""
    try:
        with open(BOARD_COMMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_chat_messages():
    """채팅 메시지 불러오기"""
    if os.path.exists(CHAT_MESSAGES_FILE):
        try:
            with open(CHAT_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_chat_messages(messages):
    """채팅 메시지 저장하기"""
    try:
        with open(CHAT_MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # 이미 로그인된 경우 홈으로 리다이렉트
    if 'user' in session and session.get('user'):
        flash('이미 로그인되어 있습니다.', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 회원가입 데이터 수집
        name = request.form.get('name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        birthday = request.form.get('birthday', '').strip()
        gender = request.form.get('gender', '').strip()
        status = request.form.get('status', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"[회원가입 시도] 학번: {student_id}, 이름: {name}, 이메일: {email}")
        
        # 필수 필드 검증
        if not all([name, student_id, birthday, gender, status, email, password]):
            flash('모든 필수 항목을 입력해주세요.', 'error')
            print("[회원가입 실패] 필수 항목 누락")
            return redirect(url_for('register'))
        
        # 학번 형식 검증 (9자리 숫자)
        if not student_id.isdigit() or len(student_id) != 9:
            flash('학번은 9자리 숫자여야 합니다.', 'error')
            print(f"[회원가입 실패] 잘못된 학번 형식: {student_id}")
            return redirect(url_for('register'))
        
        # 이메일 형식 검증
        if not email.endswith('@bible.ac.kr'):
            flash('@bible.ac.kr 도메인 이메일만 사용 가능합니다.', 'error')
            print(f"[회원가입 실패] 잘못된 이메일 형식: {email}")
            return redirect(url_for('register'))
        
        # 학번 중복 체크
        if is_student_id_duplicate(student_id):
            flash('이미 존재하는 학번입니다. 다른 학번으로 회원가입해주세요.', 'error')
            print(f"[회원가입 실패] 중복된 학번: {student_id}")
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
            print("[회원가입 실패] 데이터 저장 오류")
            return redirect(url_for('register'))
        
        # 회원가입 성공
        print(f"[회원가입 성공] 학번: {student_id}, 이름: {name}")
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    # 이미 로그인된 경우 홈으로 리다이렉트
    if 'user' in session and session.get('user'):
        flash('이미 로그인되어 있습니다.', 'info')
        return redirect(url_for('index'))
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
    
    # 현재 사용자의 익명 프로필 가져오기
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    anon_profile = {}
    if student_id:
        all_profiles = load_anon_profiles()
        user_profile = next((p for p in all_profiles if p.get('student_id') == student_id), None)
        if user_profile:
            anon_profile = user_profile
    
    return render_template('mypage.html', anon_profile=anon_profile)

@app.route('/chat')
def chat():
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    # 현재 사용자의 익명 프로필 가져오기
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    anon_profile = {}
    if student_id:
        all_profiles = load_anon_profiles()
        user_profile = next((p for p in all_profiles if p.get('student_id') == student_id), None)
        if user_profile:
            anon_profile = user_profile
        else:
            # 익명 프로필이 없으면 프로필 설정 페이지로 리디렉션
            flash('먼저 익명 프로필을 만들어주세요!', 'info')
            return redirect(url_for('profile_setup'))
    
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
    
    # 익명 프로필도 삭제
    anon_profiles = load_anon_profiles()
    anon_profiles = [p for p in anon_profiles if p.get('student_id') != student_id]
    save_anon_profiles(anon_profiles)
    
    # 세션 삭제
    session.clear()
    
    return jsonify({
        'success': True, 
        'message': '회원 탈퇴가 완료되었습니다. 그동안 이용해주셔서 감사합니다.',
        'redirect': url_for('index')
    })

@app.route('/api/anon-profiles', methods=['GET'])
def get_anon_profiles():
    """익명 프로필 목록 조회 (자신 제외)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 모든 익명 프로필 로드
    all_profiles = load_anon_profiles()
    
    # 자신의 프로필 제외
    other_profiles = [p for p in all_profiles if p.get('student_id') != current_student_id]
    
    # student_id 정보는 제거하고 반환 (보안)
    safe_profiles = []
    for profile in other_profiles:
        safe_profiles.append({
            'nickname': profile.get('nickname', '익명의친구'),
            'year': profile.get('year', ''),
            'gender': profile.get('gender', ''),
            'bio': profile.get('bio', ''),
            'interests': profile.get('interests', []),
            'avatar': profile.get('avatar', '익')
        })
    
    return jsonify({'success': True, 'profiles': safe_profiles})

@app.route('/api/interest-counts', methods=['GET'])
def get_interest_counts():
    """관심사별 참여자 수 및 닉네임 목록 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    # 모든 익명 프로필 로드
    all_profiles = load_anon_profiles()
    
    # 관심사별 카운트 및 닉네임 목록 계산
    interest_counts = {}
    interest_users = {}
    
    for profile in all_profiles:
        interests = profile.get('interests', [])
        nickname = profile.get('nickname', '익명의친구')
        
        for interest in interests:
            # 카운트 증가
            if interest not in interest_counts:
                interest_counts[interest] = 0
            interest_counts[interest] += 1
            
            # 닉네임 목록에 추가
            if interest not in interest_users:
                interest_users[interest] = []
            interest_users[interest].append(nickname)
    
    return jsonify({
        'success': True, 
        'interest_counts': interest_counts,
        'interest_users': interest_users
    })

@app.route('/api/board-posts', methods=['GET'])
def get_board_posts():
    """게시글 목록 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    posts = load_board_posts()
    return jsonify({'success': True, 'posts': posts})

@app.route('/api/board-posts', methods=['POST'])
def create_board_post():
    """게시글 작성"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    data = request.get_json()
    post_id = data.get('id')
    
    # 게시글 데이터 로드
    posts = load_board_posts()
    
    # 중복 게시글 확인 (같은 ID가 이미 있으면 추가하지 않음)
    existing_post = next((p for p in posts if p.get('id') == post_id), None)
    if existing_post:
        return jsonify({'success': True, 'message': '게시글이 이미 존재합니다.', 'post': existing_post})
    
    # 새 게시글 추가
    posts.append(data)
    
    # 저장
    if not save_board_posts(posts):
        return jsonify({'success': False, 'message': '게시글 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'message': '게시글이 작성되었습니다.', 'post': data})

@app.route('/api/board-posts/<post_id>', methods=['DELETE'])
def delete_board_post(post_id):
    """게시글 삭제"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    posts = load_board_posts()
    
    # 게시글 삭제
    posts = [p for p in posts if p.get('id') != post_id]
    
    # 저장
    if not save_board_posts(posts):
        return jsonify({'success': False, 'message': '게시글 삭제 중 오류가 발생했습니다.'}), 500
    
    # 해당 게시글의 댓글도 삭제
    comments = load_board_comments()
    comments = [c for c in comments if c.get('postId') != post_id]
    save_board_comments(comments)
    
    return jsonify({'success': True, 'message': '게시글이 삭제되었습니다.'})

@app.route('/api/board-comments', methods=['GET'])
def get_board_comments():
    """댓글 목록 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    comments = load_board_comments()
    return jsonify({'success': True, 'comments': comments})

@app.route('/api/board-comments', methods=['POST'])
def create_board_comment():
    """댓글 작성"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    data = request.get_json()
    
    # 댓글 데이터 로드
    comments = load_board_comments()
    
    # 새 댓글 추가
    comments.append(data)
    
    # 저장
    if not save_board_comments(comments):
        return jsonify({'success': False, 'message': '댓글 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'message': '댓글이 작성되었습니다.', 'comment': data})

@app.route('/api/board-comments/<comment_id>', methods=['DELETE'])
def delete_board_comment(comment_id):
    """댓글 삭제"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    comments = load_board_comments()
    
    # 댓글 찾기
    comment = next((c for c in comments if c.get('id') == comment_id), None)
    
    if not comment:
        return jsonify({'success': False, 'message': '댓글을 찾을 수 없습니다.'}), 404
    
    # 댓글 삭제
    comments = [c for c in comments if c.get('id') != comment_id]
    
    # 저장
    if not save_board_comments(comments):
        return jsonify({'success': False, 'message': '댓글 삭제 중 오류가 발생했습니다.'}), 500
    
    # 해당 게시글의 댓글 수 감소
    post_id = comment.get('postId')
    if post_id:
        posts = load_board_posts()
        post = next((p for p in posts if p.get('id') == post_id), None)
        if post and post.get('comments', 0) > 0:
            post['comments'] = post['comments'] - 1
            save_board_posts(posts)
    
    return jsonify({'success': True, 'message': '댓글이 삭제되었습니다.'})

@app.route('/api/board-posts/<post_id>', methods=['PUT'])
def update_board_post(post_id):
    """게시글 정보 업데이트 (좋아요, 댓글 수 등)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    posts = load_board_posts()
    
    # 게시글 찾기
    post = next((p for p in posts if p.get('id') == post_id), None)
    
    if not post:
        return jsonify({'success': False, 'message': '게시글을 찾을 수 없습니다.'}), 404
    
    # 업데이트할 데이터
    data = request.get_json()
    if 'likes' in data:
        post['likes'] = data['likes']
    if 'comments' in data:
        post['comments'] = data['comments']
    if 'views' in data:
        post['views'] = data['views']
    
    # 저장
    if not save_board_posts(posts):
        return jsonify({'success': False, 'message': '게시글 업데이트 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'post': post})

@app.route('/api/board-posts/<post_id>/like', methods=['POST'])
def toggle_post_like(post_id):
    """게시글 좋아요 토글"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    posts = load_board_posts()
    
    # 게시글 찾기
    post = next((p for p in posts if p.get('id') == post_id), None)
    
    if not post:
        return jsonify({'success': False, 'message': '게시글을 찾을 수 없습니다.'}), 404
    
    # 좋아요 수 업데이트
    data = request.get_json()
    post['likes'] = data.get('likes', 0)
    
    # 저장
    if not save_board_posts(posts):
        return jsonify({'success': False, 'message': '좋아요 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'likes': post['likes']})

@app.route('/api/board-comments/<comment_id>/like', methods=['POST'])
def toggle_comment_like(comment_id):
    """댓글 좋아요 토글"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    comments = load_board_comments()
    
    # 댓글 찾기
    comment = next((c for c in comments if c.get('id') == comment_id), None)
    
    if not comment:
        return jsonify({'success': False, 'message': '댓글을 찾을 수 없습니다.'}), 404
    
    # 좋아요 수 업데이트
    data = request.get_json()
    comment['likes'] = data.get('likes', 0)
    
    # 저장
    if not save_board_comments(comments):
        return jsonify({'success': False, 'message': '좋아요 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'likes': comment['likes']})

@app.route('/api/chat/messages/<room_id>', methods=['GET'])
def get_chat_messages(room_id):
    """채팅방 메시지 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    all_messages = load_chat_messages()
    room_messages = all_messages.get(room_id, [])
    
    print(f"[채팅] {room_id} 방의 메시지 조회: {len(room_messages)}개")
    
    return jsonify({'success': True, 'messages': room_messages})

@app.route('/api/chat/messages/<room_id>', methods=['POST'])
def send_chat_message(room_id):
    """채팅 메시지 전송"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    sender_nickname = data.get('sender_nickname', '익명')
    
    if not message:
        return jsonify({'success': False, 'message': '메시지를 입력해주세요.'}), 400
    
    # 모든 메시지 로드
    all_messages = load_chat_messages()
    
    # 해당 채팅방의 메시지 가져오기
    if room_id not in all_messages:
        all_messages[room_id] = []
    
    # 새 메시지 추가
    new_message = {
        'id': 'm' + str(int(time.time() * 1000)),
        'sender': sender_nickname,
        'content': message,
        'timestamp': time.time(),
        'created_at': datetime.now().isoformat()
    }
    
    all_messages[room_id].append(new_message)
    
    print(f"[채팅] {sender_nickname}님이 {room_id} 방에 메시지 전송: {message[:20]}...")
    print(f"[채팅] {room_id} 방의 총 메시지 수: {len(all_messages[room_id])}개")
    
    # 최근 100개 메시지만 유지
    if len(all_messages[room_id]) > 100:
        all_messages[room_id] = all_messages[room_id][-100:]
    
    # 저장
    if not save_chat_messages(all_messages):
        return jsonify({'success': False, 'message': '메시지 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'message_data': new_message})

@app.route('/api/check-nickname', methods=['POST'])
def check_nickname():
    """닉네임 중복 체크 API"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    data = request.get_json()
    nickname = data.get('nickname', '').strip()
    
    if not nickname:
        return jsonify({'available': True})
    
    # 모든 익명 프로필 로드
    all_profiles = load_anon_profiles()
    
    # 자신의 현재 닉네임 제외하고 중복 체크
    is_duplicate = any(
        p.get('nickname') == nickname and p.get('student_id') != current_student_id
        for p in all_profiles
    )
    
    return jsonify({
        'available': not is_duplicate,
        'message': '이미 사용 중인 닉네임입니다.' if is_duplicate else '사용 가능한 닉네임입니다.'
    })

@app.route('/api/save-anon-profile', methods=['POST'])
def save_anon_profile_api():
    """익명 프로필 저장 API (마이페이지에서 사용)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    data = request.get_json()
    nickname = data.get('nickname', '익명의친구')
    year = data.get('year')
    gender = data.get('gender')
    bio = data.get('bio', '')
    interests = data.get('interests', [])
    
    if not year or not gender or not interests:
        return jsonify({'success': False, 'message': '필수 정보를 입력해주세요.'}), 400
    
    # 익명 프로필 저장
    profiles = load_anon_profiles()
    
    # 기존 프로필 업데이트 또는 새로 추가
    existing_index = next((i for i, p in enumerate(profiles) if p.get('student_id') == student_id), None)
    
    profile_data = {
        'student_id': student_id,
        'nickname': nickname,
        'year': year,
        'gender': gender,
        'bio': bio,
        'interests': interests,
        'avatar': nickname[0] if nickname else '익'
    }
    
    if existing_index is not None:
        profiles[existing_index] = profile_data
    else:
        profiles.append(profile_data)
    
    if not save_anon_profiles(profiles):
        return jsonify({'success': False, 'message': '프로필 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'message': '익명 프로필이 저장되었습니다.'})

@app.route('/api/anon-profile', methods=['GET'])
def get_anon_profile_api():
    """현재 로그인한 사용자의 익명 프로필 가져오기"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 익명 프로필 조회
    profiles = load_anon_profiles()
    user_profile = next((p for p in profiles if p.get('student_id') == student_id), None)
    
    if user_profile:
        return jsonify({'success': True, 'profile': user_profile})
    else:
        return jsonify({'success': False, 'message': '익명 프로필이 없습니다.', 'profile': None})

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """현재 로그인한 사용자 정보 반환"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    user = session.get('user', {})
    return jsonify({
        'success': True, 
        'user': {
            'name': user.get('name'),
            'student_id': user.get('student_id'),
            'gender': user.get('gender'),
            'birthday': user.get('birthday'),
            'status': user.get('status'),
            'email': user.get('email'),
            'department': user.get('department')
        }
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
        
        # 파일에도 저장 (랜덤채팅에서 사용)
        current_user = session.get('user', {})
        student_id = current_user.get('student_id')
        
        if student_id:
            profiles = load_anon_profiles()
            
            # 기존 프로필 업데이트 또는 새로 추가
            existing_index = next((i for i, p in enumerate(profiles) if p.get('student_id') == student_id), None)
            
            profile_data = {
                'student_id': student_id,
                'nickname': nickname,
                'year': year,
                'gender': gender,
                'bio': bio,
                'interests': interests,
                'avatar': nickname[0] if nickname else '익'
            }
            
            if existing_index is not None:
                profiles[existing_index] = profile_data
            else:
                profiles.append(profile_data)
            
            save_anon_profiles(profiles)
        
        flash('익명 프로필이 저장되었습니다!', 'success')
        # 채팅 페이지로 리디렉트
        return redirect(url_for('chat'))
    
    return render_template('profile-setup.html')

if __name__ == '__main__':
    app.run(debug=True)
