from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'change-me'

# 세션 설정 - 브라우저를 닫아도 로그인 유지
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30일 동안 로그인 유지
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # HTTPS 사용 시 True로 변경

# 데이터 저장 파일 경로
DATA_FILE = 'registered_users.json'
ANON_PROFILES_FILE = 'anon_profiles.json'
BOARD_POSTS_FILE = 'board_posts.json'
BOARD_COMMENTS_FILE = 'board_comments.json'
CHAT_MESSAGES_FILE = 'chat_messages.json'
USER_READ_STATUS_FILE = 'user_read_status.json'
GROUP_MATCHING_FILE = 'group_matching.json'
GROUP_ROOMS_FILE = 'group_rooms.json'

def load_users():
    """등록된 사용자 정보 불러오기"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[사용자 데이터 로드 실패] 오류: {e}")
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

def load_user_read_status():
    """사용자별 읽음 상태 불러오기"""
    if os.path.exists(USER_READ_STATUS_FILE):
        try:
            with open(USER_READ_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_read_status(read_status):
    """사용자별 읽음 상태 저장하기"""
    try:
        with open(USER_READ_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(read_status, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def update_user_read_status(student_id, room_id, last_message_id):
    """사용자의 특정 채팅방 읽음 상태 업데이트"""
    read_status = load_user_read_status()
    
    if student_id not in read_status:
        read_status[student_id] = {}
    
    read_status[student_id][room_id] = last_message_id
    return save_user_read_status(read_status)

def get_unread_message_count(student_id, room_id):
    """사용자의 특정 채팅방 읽지 않은 메시지 수 계산"""
    # 채팅방의 모든 메시지 로드
    all_messages = load_chat_messages()
    room_messages = all_messages.get(room_id, [])
    
    print(f"[읽지 않은 메시지 계산] 방 ID: {room_id}, 총 메시지: {len(room_messages)}개")
    
    if not room_messages:
        return 0
    
    # 사용자의 읽음 상태 로드
    read_status = load_user_read_status()
    user_read_status = read_status.get(student_id, {})
    last_read_message_id = user_read_status.get(room_id)
    
    print(f"[읽지 않은 메시지 계산] 사용자: {student_id}, 마지막 읽은 메시지 ID: {last_read_message_id}")
    
    if not last_read_message_id:
        # 읽은 메시지가 없으면 모든 메시지가 읽지 않은 상태
        print(f"[읽지 않은 메시지 계산] 읽은 메시지가 없음, 전체 메시지 수 반환: {len(room_messages)}")
        return len(room_messages)
    
    # 마지막 읽은 메시지 이후의 메시지 수 계산
    unread_count = 0
    found_last_read = False
    
    for message in room_messages:
        if message.get('id') == last_read_message_id:
            found_last_read = True
            continue
        
        if found_last_read:
            unread_count += 1
    
    # 마지막 읽은 메시지를 찾지 못한 경우 모든 메시지가 읽지 않은 상태
    if not found_last_read:
        print(f"[읽지 않은 메시지 계산] 마지막 읽은 메시지를 찾지 못함, 전체 메시지 수 반환: {len(room_messages)}")
        return len(room_messages)
    
    print(f"[읽지 않은 메시지 계산] 읽지 않은 메시지 수: {unread_count}개")
    return unread_count

def load_matching_queue():
    """매칭 대기열 로드"""
    try:
        with open('matching_queue.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'waiting': [], 'matched': []}
    except Exception as e:
        print(f"매칭 대기열 로드 실패: {e}")
        return {'waiting': [], 'matched': []}

def save_matching_queue(data):
    """매칭 대기열 저장"""
    try:
        with open('matching_queue.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"매칭 대기열 저장 실패: {e}")
        return False

def load_chat_rooms():
    """채팅방 정보 로드"""
    try:
        with open('chat_rooms.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"채팅방 정보 로드 실패: {e}")
        return {}

def save_chat_rooms(rooms):
    """채팅방 정보 저장"""
    try:
        with open('chat_rooms.json', 'w', encoding='utf-8') as f:
            json.dump(rooms, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"채팅방 정보 저장 실패: {e}")
        return False

def load_group_matching():
    """그룹 매칭 대기열 불러오기"""
    if os.path.exists(GROUP_MATCHING_FILE):
        try:
            with open(GROUP_MATCHING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[그룹 매칭 로드 실패] 오류: {e}")
            return {'male': [], 'female': [], 'groups': []}
    return {'male': [], 'female': [], 'groups': []}

def save_group_matching(data):
    """그룹 매칭 대기열 저장하기"""
    try:
        with open(GROUP_MATCHING_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[그룹 매칭 저장 실패] 오류: {e}")
        return False

def load_group_rooms():
    """그룹 채팅방 정보 불러오기"""
    if os.path.exists(GROUP_ROOMS_FILE):
        try:
            with open(GROUP_ROOMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[그룹 채팅방 로드 실패] 오류: {e}")
            return {}
    return {}

def save_group_rooms(rooms):
    """그룹 채팅방 정보 저장하기"""
    try:
        with open(GROUP_ROOMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(rooms, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[그룹 채팅방 저장 실패] 오류: {e}")
        return False

def try_matching(matching_data):
    """매칭 시도 (이성 매칭)"""
    waiting_list = matching_data.get('waiting', [])
    
    if len(waiting_list) < 2:
        return None
    
    # 이성 매칭 시도
    for i, user1 in enumerate(waiting_list):
        for j, user2 in enumerate(waiting_list[i+1:], i+1):
            if user1.get('gender') != user2.get('gender'):
                # 매칭 성공
                room_id = f"dm_{int(time.time() * 1000)}"
                
                # 채팅방 생성
                room_data = {
                    'room_id': room_id,
                    'user1_id': user1['student_id'],
                    'user2_id': user2['student_id'],
                    'user1_nickname': user1['nickname'],
                    'user2_nickname': user2['nickname'],
                    'created_at': time.time(),
                    'user1_entered': False,
                    'user2_entered': False,
                    'user1_entered_at': None,
                    'user2_entered_at': None,
                    'active': True
                }
                
                # 방 정보 저장
                rooms_data = load_chat_rooms()
                rooms_data[room_id] = room_data
                save_chat_rooms(rooms_data)
                
                # 대기열에서 제거 (정확한 필터링)
                matching_data['waiting'] = [
                    w for w in waiting_list 
                    if w.get('student_id') not in [user1['student_id'], user2['student_id']]
                ]
                save_matching_queue(matching_data)
                
                print(f"[매칭 성공] {user1['nickname']} ↔ {user2['nickname']} (방 ID: {room_id})")
                
                return {
                    'room_id': room_id,
                    'user1': user1,
                    'user2': user2
                }
    
    return None

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
                    
                    # 세션을 영구적으로 설정 (브라우저를 닫아도 유지)
                    session.permanent = True
                    
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
                    # 세션을 영구적으로 설정 (브라우저를 닫아도 유지)
                    session.permanent = True
                    
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
    print(f"[회원 탈퇴 요청] 세션 정보: {session}")
    
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        print("[회원 탈퇴 실패] 로그인되지 않은 사용자")
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    student_id = current_user.get('student_id')
    
    print(f"[회원 탈퇴] 요청한 사용자 학번: {student_id}")
    
    if not student_id:
        print("[회원 탈퇴 실패] 학번 정보 없음")
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 사용자 데이터 로드
    users = load_users()
    print(f"[회원 탈퇴] 현재 등록된 사용자 수: {len(users)}")
    
    # 해당 사용자 찾아서 삭제
    original_count = len(users)
    users = [user for user in users if user.get('student_id') != student_id]
    deleted_count = original_count - len(users)
    
    print(f"[회원 탈퇴] 삭제된 사용자 수: {deleted_count}")
    
    if len(users) == original_count:
        # 사용자를 찾지 못한 경우 (등록되지 않은 사용자일 수 있음)
        print("[회원 탈퇴] 사용자를 찾지 못함 - 세션만 삭제")
        session.clear()
        return jsonify({
            'success': True, 
            'message': '회원 탈퇴가 완료되었습니다.',
            'redirect': url_for('index')
        })
    
    # 변경된 사용자 목록 저장
    print(f"[회원 탈퇴] 사용자 목록 저장 시도 - {len(users)}명")
    if not save_users(users):
        print("[회원 탈퇴 실패] 사용자 데이터 저장 실패")
        return jsonify({'success': False, 'message': '회원 탈퇴 중 오류가 발생했습니다.'}), 500
    
    # 익명 프로필도 삭제
    try:
        anon_profiles = load_anon_profiles()
        original_anon_count = len(anon_profiles)
        anon_profiles = [p for p in anon_profiles if p.get('student_id') != student_id]
        deleted_anon_count = original_anon_count - len(anon_profiles)
        save_anon_profiles(anon_profiles)
        print(f"[회원 탈퇴] 익명 프로필 삭제: {deleted_anon_count}개")
    except Exception as e:
        print(f"[회원 탈퇴] 익명 프로필 삭제 중 오류: {e}")
    
    # 세션 삭제
    session.clear()
    print(f"[회원 탈퇴 성공] 학번 {student_id} 탈퇴 완료")
    
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
    """게시글 정보 업데이트 (좋아요, 댓글 수, 제목, 내용 등)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    posts = load_board_posts()
    
    # 게시글 찾기
    post = next((p for p in posts if p.get('id') == post_id), None)
    
    if not post:
        return jsonify({'success': False, 'message': '게시글을 찾을 수 없습니다.'}), 404
    
    # 업데이트할 데이터
    data = request.get_json()
    
    # 게시글 내용 수정인 경우 작성자 확인
    if 'title' in data or 'content' in data:
        if post.get('authorStudentId') != current_student_id:
            return jsonify({'success': False, 'message': '게시글 작성자만 수정할 수 있습니다.'}), 403
        
        # 제목과 내용 업데이트
        if 'title' in data:
            post['title'] = data['title']
        if 'content' in data:
            post['content'] = data['content']
        if 'tags' in data:
            post['tags'] = data['tags']
        
        # 수정 시간 기록
        post['updatedAt'] = datetime.now().isoformat()
    
    # 통계 정보 업데이트 (작성자 확인 불필요)
    if 'likes' in data:
        post['likes'] = data['likes']
    if 'comments' in data:
        post['comments'] = data['comments']
    if 'views' in data:
        post['views'] = data['views']
    
    # 저장
    if not save_board_posts(posts):
        return jsonify({'success': False, 'message': '게시글 업데이트 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'post': post, 'message': '게시글이 수정되었습니다.'})

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
        'created_at': datetime.now().isoformat(),
        'type': 'text'
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

@app.route('/api/chat/read-status/<room_id>', methods=['POST'])
def update_read_status(room_id):
    """채팅방 읽음 상태 업데이트"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 해당 채팅방의 최신 메시지 ID 가져오기
    all_messages = load_chat_messages()
    room_messages = all_messages.get(room_id, [])
    
    if not room_messages:
        return jsonify({'success': True, 'message': '메시지가 없습니다.'})
    
    # 가장 최근 메시지 ID
    latest_message_id = room_messages[-1].get('id')
    
    # 읽음 상태 업데이트
    if update_user_read_status(current_student_id, room_id, latest_message_id):
        print(f"[읽음 상태 업데이트] 사용자: {current_student_id}, 방: {room_id}, 메시지: {latest_message_id}")
        return jsonify({
            'success': True, 
            'message': '읽음 상태가 업데이트되었습니다.',
            'last_read_message_id': latest_message_id
        })
    else:
        return jsonify({'success': False, 'message': '읽음 상태 업데이트에 실패했습니다.'}), 500

@app.route('/api/chat/unread-count/<room_id>', methods=['GET'])
def get_unread_count(room_id):
    """채팅방 읽지 않은 메시지 수 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    unread_count = get_unread_message_count(current_student_id, room_id)
    
    return jsonify({
        'success': True,
        'room_id': room_id,
        'unread_count': unread_count
    })

@app.route('/api/chat/leave/<room_id>', methods=['POST'])
def leave_chat_room(room_id):
    """채팅방 나가기 (나가기 메시지 전송)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    data = request.get_json()
    nickname = data.get('nickname', '익명').strip()
    
    if not nickname:
        return jsonify({'success': False, 'message': '닉네임이 필요합니다.'}), 400
    
    # 모든 메시지 로드
    all_messages = load_chat_messages()
    
    # 해당 채팅방의 메시지 가져오기
    if room_id not in all_messages:
        all_messages[room_id] = []
    
    # 나가기 메시지 추가
    leave_message = {
        'id': 'leave_' + str(int(time.time() * 1000)),
        'sender': '시스템',
        'content': f'{nickname}님이 채팅방을 나갔습니다.',
        'timestamp': time.time(),
        'created_at': datetime.now().isoformat(),
        'type': 'leave'
    }
    
    all_messages[room_id].append(leave_message)
    
    print(f"[채팅] {nickname}님이 {room_id} 방을 나감")
    
    # 최근 100개 메시지만 유지
    if len(all_messages[room_id]) > 100:
        all_messages[room_id] = all_messages[room_id][-100:]
    
    # 저장
    if not save_chat_messages(all_messages):
        return jsonify({'success': False, 'message': '나가기 메시지 저장 중 오류가 발생했습니다.'}), 500
    
    return jsonify({'success': True, 'message_data': leave_message})

@app.route('/api/interest/<interest_name>/leave', methods=['POST'])
def leave_interest_room(interest_name):
    """관심분야 방에서 나가기 (참여자 수 감소)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 현재 사용자의 익명 프로필 가져오기
    user_profile = None
    all_profiles = load_anon_profiles()
    for profile in all_profiles:
        if profile.get('student_id') == current_student_id:
            user_profile = profile
            break
    
    if not user_profile:
        return jsonify({'success': False, 'message': '익명 프로필을 찾을 수 없습니다.'}), 404
    
    # 관심사에서 해당 관심분야 제거
    if interest_name in user_profile.get('interests', []):
        user_profile['interests'].remove(interest_name)
        
        # 서버에 저장
        save_anon_profiles(all_profiles)
        
        print(f"[관심분야] {user_profile.get('nickname', '익명')}님이 {interest_name} 방에서 나감")
        
        return jsonify({
            'success': True, 
            'message': f'{interest_name} 방에서 나갔습니다.',
            'remaining_interests': user_profile.get('interests', [])
        })
    else:
        return jsonify({'success': False, 'message': '해당 관심분야 방에 참여하지 않았습니다.'}), 400

@app.route('/api/matching/start', methods=['POST'])
def start_matching():
    """1:1 매칭 시작"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 현재 사용자의 익명 프로필 가져오기
    user_profile = None
    all_profiles = load_anon_profiles()
    for profile in all_profiles:
        if profile.get('student_id') == current_student_id:
            user_profile = profile
            break
    
    if not user_profile:
        return jsonify({'success': False, 'message': '익명 프로필을 찾을 수 없습니다.'}), 404
    
    # 매칭 대기열에 추가
    matching_data = load_matching_queue()
    
    # 이미 대기 중인지 확인
    existing_wait = next((w for w in matching_data.get('waiting', []) if w.get('student_id') == current_student_id), None)
    if existing_wait:
        return jsonify({'success': False, 'message': '이미 매칭 대기 중입니다.'}), 400
    
    # 이미 매칭된 방이 있는지 확인 (활성화된 방만)
    rooms_data = load_chat_rooms()
    existing_room = None
    for room_id, room in rooms_data.items():
        # 비활성화된 방은 제외
        if room.get('active', True) == False:
            continue
            
        if current_student_id in [room.get('user1_id'), room.get('user2_id')]:
            # 방이 아직 활성 상태인지 확인 (나가기하지 않은 상태)
            existing_room = room
            break
    
    if existing_room:
        other_student_id = existing_room['user2_id'] if current_student_id == existing_room['user1_id'] else existing_room['user1_id']
        other_nickname = existing_room['user2_nickname'] if current_student_id == existing_room['user1_id'] else existing_room['user1_nickname']
        
        return jsonify({
            'success': False, 
            'message': f'이미 {other_nickname}님과 매칭된 방이 있습니다.',
            'existing_room': {
                'room_id': existing_room['room_id'],
                'other_nickname': other_nickname
            }
        }), 400
    
    # 대기열에 추가
    waiting_user = {
        'student_id': current_student_id,
        'nickname': user_profile.get('nickname'),
        'gender': user_profile.get('gender'),
        'joined_at': time.time()
    }
    
    matching_data['waiting'].append(waiting_user)
    save_matching_queue(matching_data)
    
    print(f"[매칭] {user_profile.get('nickname')}님이 1:1 매칭 대기열에 추가됨")
    
    # 매칭 시도
    match_result = try_matching(matching_data)
    
    return jsonify({
        'success': True,
        'message': '매칭 대기열에 추가되었습니다.',
        'matched': match_result is not None,
        'match_data': match_result
    })

@app.route('/api/matching/cancel', methods=['POST'])
def cancel_matching():
    """1:1 매칭 취소"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    matching_data = load_matching_queue()
    
    # 대기열에서 제거
    matching_data['waiting'] = [w for w in matching_data.get('waiting', []) if w.get('student_id') != current_student_id]
    save_matching_queue(matching_data)
    
    print(f"[매칭] {current_student_id}님이 매칭 대기열에서 제거됨")
    
    return jsonify({'success': True, 'message': '매칭이 취소되었습니다.'})

@app.route('/api/room/<room_id>/enter', methods=['POST'])
def enter_room(room_id):
    """채팅방 입장"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 방 정보 가져오기
    rooms_data = load_chat_rooms()
    room = rooms_data.get(room_id)
    
    if not room:
        print(f"[에러] 존재하지 않는 방: {room_id}")
        return jsonify({'success': False, 'message': '채팅방을 찾을 수 없습니다.'}), 404
    
    # 비활성화된 방 체크
    if room.get('active', True) == False:
        print(f"[에러] 비활성화된 방 접근 시도: {room_id} (사용자: {current_student_id})")
        return jsonify({'success': False, 'message': '비활성화된 방입니다.'}), 403
    
    # 사용자가 이 방에 참여할 수 있는지 확인
    if current_student_id not in [room['user1_id'], room['user2_id']]:
        print(f"[에러] 권한 없는 방 접근 시도: {room_id} (사용자: {current_student_id})")
        return jsonify({'success': False, 'message': '이 방에 참여할 권한이 없습니다.'}), 403
    
    # 입장 상태 업데이트 (멱등 처리)
    is_first_join = False
    if current_student_id == room['user1_id']:
        if not room.get('user1_entered', False):
            room['user1_entered'] = True
            room['user1_entered_at'] = time.time()
            is_first_join = True
    else:
        if not room.get('user2_entered', False):
            room['user2_entered'] = True
            room['user2_entered_at'] = time.time()
            is_first_join = True
    
    rooms_data[room_id] = room
    save_chat_rooms(rooms_data)
    
    # 입장 메시지 생성 (멱등 처리)
    user_profile = None
    all_profiles = load_anon_profiles()
    for profile in all_profiles:
        if profile.get('student_id') == current_student_id:
            user_profile = profile
            break
    
    nickname = user_profile.get('nickname', '익명') if user_profile else '익명'
    
    # 상대방이 이미 입장했는지 확인
    other_user_entered = False
    if current_student_id == room['user1_id']:
        other_user_entered = room.get('user2_entered', False)
    else:
        other_user_entered = room.get('user1_entered', False)
    
    # 첫 입장일 때만 메시지 추가 (중복 방지)
    if is_first_join:
        messages = load_chat_messages()
        if room_id not in messages:
            messages[room_id] = []
        
        # 직전 시스템 메시지 확인 (중복 방지)
        last_message = messages[room_id][-1] if messages[room_id] else None
        should_add_message = True
        
        # 두 번째 사용자 입장 시에는 wait 메시지를 enter로 교체해야 하므로 항상 처리
        if other_user_entered:
            should_add_message = True
        elif last_message and last_message.get('type') in ['wait', 'enter']:
            # 첫 번째 사용자 입장 시에만 중복 방지
            should_add_message = False
        
        if should_add_message:
            if other_user_entered:
                # 두 번째 사용자 입장 시: 기존 wait 메시지를 enter 메시지로 교체
                enter_message = {
                    'id': f"enter_{int(time.time() * 1000)}",
                    'sender': '시스템',
                    'content': f'{nickname}님이 방에 입장했습니다.',
                    'timestamp': time.time(),
                    'created_at': datetime.now().isoformat(),
                    'type': 'enter'
                }
                
                # 기존 wait 메시지가 있으면 교체, 없으면 추가
                if last_message and last_message.get('type') == 'wait':
                    # 마지막 메시지가 wait 타입이면 교체
                    messages[room_id][-1] = enter_message
                    print(f"[입장] {nickname}님이 {room_id} 방에 입장 (wait 메시지를 enter로 교체)")
                else:
                    # wait 메시지가 없으면 새로 추가
                    messages[room_id].append(enter_message)
                    print(f"[입장] {nickname}님이 {room_id} 방에 입장 (상대방 이미 입장함)")
            else:
                # 첫 번째 입장자에게만 메시지
                wait_message = {
                    'id': f"wait_{int(time.time() * 1000)}",
                    'sender': '시스템',
                    'content': '상대방이 아직 방에 입장하지 않았습니다.',
                    'timestamp': time.time(),
                    'created_at': datetime.now().isoformat(),
                    'type': 'wait'
                }
                messages[room_id].append(wait_message)
                print(f"[입장] {nickname}님이 {room_id} 방에 입장 (첫 번째 입장자)")
        
        # 메시지 저장
        save_chat_messages(messages)
    else:
        print(f"[입장] {nickname}님이 {room_id} 방에 재입장 (이미 입장한 상태)")
    
    return jsonify({
        'success': True,
        'message': '방에 입장했습니다.',
        'room_data': room,
        'other_user_entered': other_user_entered
    })

@app.route('/api/room/<room_id>/leave', methods=['POST'])
def leave_room(room_id):
    """채팅방 나가기 (방 비활성화)"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 방 정보 가져오기
    rooms_data = load_chat_rooms()
    room = rooms_data.get(room_id)
    
    if not room:
        return jsonify({'success': False, 'message': '채팅방을 찾을 수 없습니다.'}), 404
    
    # 사용자가 이 방에 참여할 수 있는지 확인
    if current_student_id not in [room['user1_id'], room['user2_id']]:
        return jsonify({'success': False, 'message': '이 방에 참여할 권한이 없습니다.'}), 403
    
    # 방을 비활성화 (삭제하지 않고 비활성화 상태로 표시)
    room['active'] = False
    room['left_at'] = time.time()
    room['left_by'] = current_student_id
    
    rooms_data[room_id] = room
    save_chat_rooms(rooms_data)
    
    print(f"[방 나가기] {current_student_id}님이 {room_id} 방을 나감")
    
    return jsonify({
        'success': True,
        'message': '방에서 나갔습니다.'
    })

@app.route('/api/rooms', methods=['GET'])
def get_user_rooms():
    """사용자의 채팅방 목록 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    # 모든 방 정보 가져오기
    rooms_data = load_chat_rooms()
    
    # 사용자가 참여한 방들 필터링 (활성화된 방만)
    user_rooms = []
    for room_id, room in rooms_data.items():
        # 비활성화된 방은 제외
        if room.get('active', True) == False:
            continue
            
        if current_student_id in [room.get('user1_id'), room.get('user2_id')]:
            # 상대방 정보 가져오기
            other_student_id = room['user2_id'] if current_student_id == room['user1_id'] else room['user1_id']
            other_profile = None
            
            all_profiles = load_anon_profiles()
            for profile in all_profiles:
                if profile.get('student_id') == other_student_id:
                    other_profile = profile
                    break
            
            # 읽지 않은 메시지 수 계산
            unread_count = get_unread_message_count(current_student_id, room_id)
            
            user_rooms.append({
                'room_id': room_id,
                'room_name': other_profile.get('nickname', '익명') if other_profile else '익명',
                'type': 'dm',
                'created_at': room.get('created_at'),
                'user1_entered': room.get('user1_entered', False),
                'user2_entered': room.get('user2_entered', False),
                'unread_count': unread_count
            })
    
    return jsonify({
        'success': True,
        'rooms': user_rooms
    })

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

def try_group_matching(matching_data):
    """그룹 매칭 시도 (3-6명, 남녀 비율 유지)"""
    male_queue = matching_data.get('male', [])
    female_queue = matching_data.get('female', [])
    
    total_count = len(male_queue) + len(female_queue)
    
    # 최소 3명 이상이어야 그룹 매칭 가능
    if total_count < 3:
        return None
    
    # 가능한 그룹 조합 찾기 (3-6명)
    for group_size in range(3, 7):
        for male_count in range(1, group_size):
            female_count = group_size - male_count
            
            # 비율 체크: 5:5 ~ 2:1 범위
            ratio = max(male_count, female_count) / min(male_count, female_count)
            if ratio <= 2 and male_count <= len(male_queue) and female_count <= len(female_queue):
                # 그룹 멤버 선택
                group_members = []
                
                # 남자 멤버 선택
                for i in range(male_count):
                    if male_queue:
                        group_members.append(male_queue.pop(0))
                
                # 여자 멤버 선택
                for i in range(female_count):
                    if female_queue:
                        group_members.append(female_queue.pop(0))
                
                if len(group_members) == group_size:
                    # 그룹 채팅방 생성
                    room_id = f"group_{int(time.time())}_{group_size}"
                    group_room_name = f"그룹 {len(matching_data.get('groups', [])) + 1}"
                    
                    # 그룹 채팅방 데이터 생성
                    group_room = {
                        'room_id': room_id,
                        'room_name': group_room_name,
                        'type': 'group',
                        'members': group_members,
                        'created_at': time.time(),
                        'active': True,
                        'message_count': 0
                    }
                    
                    # 그룹 채팅방 저장
                    group_rooms = load_group_rooms()
                    group_rooms[room_id] = group_room
                    save_group_rooms(group_rooms)
                    
                    # 완성된 그룹을 대기열에 저장
                    if 'groups' not in matching_data:
                        matching_data['groups'] = []
                    
                    matching_data['groups'].append({
                        'room_id': room_id,
                        'room_name': group_room_name,
                        'members': group_members,
                        'created_at': time.time()
                    })
                    
                    # 대기열 업데이트
                    matching_data['male'] = male_queue
                    matching_data['female'] = female_queue
                    save_group_matching(matching_data)
                    
                    print(f"[그룹 매칭 성공] {group_room_name} 생성 - {male_count}남 {female_count}여")
                    
                    return {
                        'room_id': room_id,
                        'room_name': group_room_name,
                        'members': group_members,
                        'male_count': male_count,
                        'female_count': female_count
                    }
    
    return None

@app.route('/api/group-matching/start', methods=['POST'])
def start_group_matching():
    """그룹 매칭 시작"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 익명 프로필 확인
    anon_profiles = load_anon_profiles()
    user_profile = next((p for p in anon_profiles if p.get('student_id') == current_student_id), None)
    
    if not user_profile:
        return jsonify({'success': False, 'message': '익명 프로필을 먼저 설정해주세요.'}), 400
    
    # 그룹 매칭 대기열 로드
    matching_data = load_group_matching()
    
    # 사용자 정보 생성
    user_info = {
        'student_id': current_student_id,
        'nickname': user_profile.get('nickname', '익명'),
        'gender': user_profile.get('gender', '남자'),
        'join_time': time.time()
    }
    
    # 이미 대기열에 있는지 확인
    existing_male = next((u for u in matching_data['male'] if u.get('student_id') == current_student_id), None)
    existing_female = next((u for u in matching_data['female'] if u.get('student_id') == current_student_id), None)
    
    if existing_male or existing_female:
        return jsonify({'success': False, 'message': '이미 그룹 매칭 대기열에 있습니다.'}), 400
    
    # 성별에 따라 대기열에 추가
    if user_info['gender'] == '남자':
        matching_data['male'].append(user_info)
    else:
        matching_data['female'].append(user_info)
    
    # 대기열 저장
    save_group_matching(matching_data)
    
    print(f"[그룹 매칭] {user_info['nickname']} ({user_info['gender']}) 대기열 추가")
    
    # 그룹 매칭 시도
    group_result = try_group_matching(matching_data)
    
    if group_result:
        return jsonify({
            'success': True,
            'matched': True,
            'group_data': group_result
        })
    else:
        return jsonify({
            'success': True,
            'matched': False,
            'message': '그룹 매칭 대기 중입니다.',
            'waiting_count': {
                'male': len(matching_data['male']),
                'female': len(matching_data['female'])
            }
        })

@app.route('/api/group-matching/cancel', methods=['POST'])
def cancel_group_matching():
    """그룹 매칭 취소"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 그룹 매칭 대기열에서 제거
    matching_data = load_group_matching()
    
    # 남자 대기열에서 제거
    matching_data['male'] = [u for u in matching_data['male'] if u.get('student_id') != current_student_id]
    # 여자 대기열에서 제거
    matching_data['female'] = [u for u in matching_data['female'] if u.get('student_id') != current_student_id]
    
    save_group_matching(matching_data)
    
    print(f"[그룹 매칭 취소] 학번 {current_student_id} 대기열에서 제거")
    
    return jsonify({
        'success': True,
        'message': '그룹 매칭이 취소되었습니다.'
    })

@app.route('/api/group-matching/status', methods=['GET'])
def get_group_matching_status():
    """그룹 매칭 상태 확인"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 그룹 매칭 대기열 로드
    matching_data = load_group_matching()
    
    # 사용자가 대기열에 있는지 확인
    in_male_queue = any(u.get('student_id') == current_student_id for u in matching_data['male'])
    in_female_queue = any(u.get('student_id') == current_student_id for u in matching_data['female'])
    
    return jsonify({
        'success': True,
        'in_queue': in_male_queue or in_female_queue,
        'waiting_count': {
            'male': len(matching_data['male']),
            'female': len(matching_data['female'])
        }
    })

@app.route('/api/group-rooms', methods=['GET'])
def get_group_rooms():
    """사용자의 그룹 채팅방 목록 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 그룹 채팅방 로드
    group_rooms = load_group_rooms()
    
    # 사용자가 참여한 그룹 채팅방만 필터링
    user_rooms = []
    for room_id, room_data in group_rooms.items():
        if room_data.get('active', True):
            members = room_data.get('members', [])
            if any(member.get('student_id') == current_student_id for member in members):
                # 읽지 않은 메시지 수 계산
                unread_count = get_unread_message_count(current_student_id, room_id)
                
                user_rooms.append({
                    'room_id': room_id,
                    'room_name': room_data.get('room_name', ''),
                    'type': 'group',
                    'member_count': len(members),
                    'created_at': room_data.get('created_at', 0),
                    'unread_count': unread_count
                })
    
    return jsonify({
        'success': True,
        'rooms': user_rooms
    })

@app.route('/api/group-messages/<room_id>', methods=['GET'])
def get_group_messages(room_id):
    """그룹 채팅방 메시지 조회"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 그룹 채팅방 확인
    group_rooms = load_group_rooms()
    room_data = group_rooms.get(room_id)
    
    if not room_data:
        return jsonify({'success': False, 'message': '채팅방을 찾을 수 없습니다.'}), 404
    
    # 사용자가 이 그룹에 참여할 수 있는지 확인
    members = room_data.get('members', [])
    if not any(member.get('student_id') == current_student_id for member in members):
        return jsonify({'success': False, 'message': '이 그룹에 참여할 권한이 없습니다.'}), 403
    
    # 메시지 로드
    messages = load_chat_messages()
    room_messages = messages.get(room_id, [])
    
    return jsonify({
        'success': True,
        'messages': room_messages
    })

@app.route('/api/group-messages/<room_id>', methods=['POST'])
def send_group_message(room_id):
    """그룹 채팅방 메시지 전송"""
    # 로그인 체크
    if 'user' not in session or not session.get('user'):
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    current_user = session.get('user', {})
    current_student_id = current_user.get('student_id')
    
    if not current_student_id:
        return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}), 400
    
    # 그룹 채팅방 확인
    group_rooms = load_group_rooms()
    room_data = group_rooms.get(room_id)
    
    if not room_data:
        return jsonify({'success': False, 'message': '채팅방을 찾을 수 없습니다.'}), 404
    
    # 사용자가 이 그룹에 참여할 수 있는지 확인
    members = room_data.get('members', [])
    user_member = next((member for member in members if member.get('student_id') == current_student_id), None)
    
    if not user_member:
        return jsonify({'success': False, 'message': '이 그룹에 참여할 권한이 없습니다.'}), 403
    
    # 메시지 데이터 수집
    data = request.get_json()
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'success': False, 'message': '메시지를 입력해주세요.'}), 400
    
    # 메시지 생성
    message = {
        'id': f"group_{room_id}_{int(time.time() * 1000)}",
        'room_id': room_id,
        'sender_id': current_student_id,
        'sender_nickname': user_member.get('nickname', '익명'),
        'message': message_text,
        'timestamp': time.time(),
        'type': 'group'
    }
    
    # 메시지 저장
    messages = load_chat_messages()
    if room_id not in messages:
        messages[room_id] = []
    
    messages[room_id].append(message)
    save_chat_messages(messages)
    
    # 그룹 채팅방 메시지 수 증가
    room_data['message_count'] = room_data.get('message_count', 0) + 1
    group_rooms[room_id] = room_data
    save_group_rooms(group_rooms)
    
    print(f"[그룹 메시지] {room_id}: {user_member.get('nickname')} - {message_text}")
    
    return jsonify({
        'success': True,
        'message': '메시지가 전송되었습니다.',
        'message_data': message
    })

if __name__ == '__main__':
    app.run(debug=True)
