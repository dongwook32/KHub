// KBU Hub 게시판 JavaScript

// ===== 전역 변수 =====
let currentBoard = 'ai_free'; // 기본값을 AI융합학부 자유게시판으로 설정
let currentDepartment = 'ai';
let posts = [];
let comments = [];
let expandedDepartments = {}; // 모든 학과는 기본으로 닫힌 상태

// ===== 익명 번호 관리 =====
let anonymousCounter = 1;

function generateAnonymousId() {
  return anonymousCounter++; // 1부터 순차적으로 부여
}

// ===== 좋아요 관리 =====
let likedPosts = new Set(); // 좋아요한 게시글 ID 저장
let likedComments = new Set(); // 좋아요한 댓글 ID 저장

function toggleLike(postId) {
  const post = posts.find(p => p.id === postId);
  if (!post) return;
  
  if (likedPosts.has(postId)) {
    // 좋아요 취소
    likedPosts.delete(postId);
    post.likes = Math.max(0, post.likes - 1);
  } else {
    // 좋아요 추가
    likedPosts.add(postId);
    post.likes += 1;
  }
  
  // UI 업데이트
  updateLikeUI(postId, post.likes);
  
  // 마이페이지 활동 기록 업데이트 (마이페이지가 열려있다면)
  if (typeof toggleMyLike === 'function') {
    toggleMyLike(post);
  }
}

function updateLikeUI(postId, likesCount) {
  // 게시글 목록에서 좋아요 버튼 업데이트
  const postElement = document.querySelector(`[data-post-id="${postId}"]`);
  if (postElement) {
    const likeBtn = postElement.querySelector('.like-btn');
    if (likeBtn) {
      const isLikedState = isLiked(postId);
      likeBtn.className = `stat-item like-btn ${isLikedState ? 'liked' : ''}`;
      likeBtn.innerHTML = `
        <svg width="16" height="16" fill="${isLikedState ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
        </svg>
        ${likesCount}
      `;
    }
  }
  
  // 게시글 상세에서 좋아요 버튼 업데이트
  if (window.currentPostId === postId) {
    const detailLikeBtn = document.querySelector('.detail-stats .like-btn');
    if (detailLikeBtn) {
      const isLikedState = isLiked(postId);
      detailLikeBtn.className = `stat-item like-btn ${isLikedState ? 'liked' : ''}`;
      detailLikeBtn.innerHTML = `
        <svg width="16" height="16" fill="${isLikedState ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
        </svg>
        ${likesCount}
      `;
    }
  }
}

function isLiked(postId) {
  return likedPosts.has(postId);
}

function toggleCommentLike(commentId) {
  const comment = comments.find(c => c.id === commentId);
  if (!comment) return;
  
  if (likedComments.has(commentId)) {
    // 좋아요 취소
    likedComments.delete(commentId);
    comment.likes = Math.max(0, comment.likes - 1);
  } else {
    // 좋아요 추가
    likedComments.add(commentId);
    comment.likes += 1;
  }
  
  // UI 업데이트
  updateCommentLikeUI(commentId, comment.likes);
  
  // 마이페이지 활동 기록 업데이트 (마이페이지가 열려있다면)
  if (typeof toggleMyCommentLike === 'function') {
    toggleMyCommentLike(comment);
  }
}

function updateCommentLikeUI(commentId, likesCount) {
  // 댓글 좋아요 버튼 업데이트
  const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
  if (commentElement) {
    const likeBtn = commentElement.querySelector('.comment-like-btn');
    if (likeBtn) {
      const isLikedState = isCommentLiked(commentId);
      likeBtn.className = `comment-like-btn ${isLikedState ? 'liked' : ''}`;
      likeBtn.innerHTML = `
        <svg width="14" height="14" fill="${isLikedState ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
        </svg>
        ${likesCount}
      `;
    }
  }
}

function isCommentLiked(commentId) {
  return likedComments.has(commentId);
}

// ===== 학번 표시 함수 =====
function getYearDisplay(year) {
  if (!year) return '익명';
  
  const currentYear = new Date().getFullYear();
  const admissionYear = 2000 + year;
  const grade = currentYear - admissionYear + 1;
  
  let status = '';
  if (grade <= 0) status = '신'; // 신입생
  else if (grade >= 5) status = '졸'; // 졸업생
  else status = '재'; // 재학생
  
  return `${year}학번(${status})`;
}

// ===== 학과 및 게시판 정보 =====
const departments = [
  { 
    id: 'ai', 
    name: 'AI융합학부', 
    icon: '🤖',
    iconText: '[AI]',
    boards: [
      { id: 'ai_free', name: '자유게시판' },
      { id: 'ai_study', name: '학습게시판' },
      { id: 'ai_jobs', name: '취업/진로' },
      { id: 'ai_market', name: '장터 게시판' }
    ]
  },
  { 
    id: 'bible', 
    name: '성서학과', 
    icon: '📚',
    iconText: '[성서]',
    boards: [
      { id: 'bible_free', name: '자유게시판' },
      { id: 'bible_study', name: '학습게시판' },
      { id: 'bible_jobs', name: '취업/진로' },
      { id: 'bible_market', name: '장터 게시판' }
    ]
  },
  { 
    id: 'nursing', 
    name: '간호학과', 
    icon: '⚕️',
    iconText: '[간호]',
    boards: [
      { id: 'nursing_free', name: '자유게시판' },
      { id: 'nursing_study', name: '학습게시판' },
      { id: 'nursing_jobs', name: '취업/진로' },
      { id: 'nursing_market', name: '장터 게시판' }
    ]
  },
  { 
    id: 'child', 
    name: '영유아보육학과', 
    icon: '🧸',
    iconText: '[보육]',
    boards: [
      { id: 'child_free', name: '자유게시판' },
      { id: 'child_study', name: '학습게시판' },
      { id: 'child_jobs', name: '취업/진로' },
      { id: 'child_market', name: '장터 게시판' }
    ]
  },
  { 
    id: 'social', 
    name: '사회복지학과', 
    icon: '🤲',
    iconText: '[복지]',
    boards: [
      { id: 'social_free', name: '자유게시판' },
      { id: 'social_study', name: '학습게시판' },
      { id: 'social_jobs', name: '취업/진로' },
      { id: 'social_market', name: '장터 게시판' }
    ]
  }
];

// ===== 목업 데이터 =====
const mockPosts = [
  // AI융합학부 - 자유게시판
  {
    id: 'p1',
    title: '머신러닝 프로젝트 팀원 모집합니다',
    author: '익명' + generateAnonymousId(),
    year: 23,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    views: 156,
    likes: 5,
    comments: 2,
    tags: ['프로젝트', 'AI'],
    boardId: 'ai_free',
    departmentId: 'ai',
    type: 'talk'
  },
  {
    id: 'p1_2',
    title: 'AI융합학부 새내기 환영합니다!',
    author: '익명' + generateAnonymousId(),
    year: 20,
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    views: 234,
    likes: 15,
    comments: 8,
    tags: ['환영', '새내기'],
    boardId: 'ai_free',
    departmentId: 'ai',
    type: 'share'
  },
  
  // AI융합학부 - 학습게시판
  {
    id: 'p2',
    title: '파이썬 기초 강의 추천해주세요',
    author: '익명' + generateAnonymousId(),
    year: 23,
    createdAt: new Date(Date.now() - 259200000).toISOString(),
    views: 189,
    likes: 8,
    comments: 5,
    tags: ['파이썬', '강의'],
    boardId: 'ai_study',
    departmentId: 'ai',
    type: 'question'
  },
  {
    id: 'p2_2',
    title: '데이터사이언스 공부 로드맵 공유',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 345600000).toISOString(),
    views: 312,
    likes: 22,
    comments: 12,
    tags: ['데이터사이언스', '로드맵'],
    boardId: 'ai_study',
    departmentId: 'ai',
    type: 'share'
  },
  
  // AI융합학부 - 취업/진로
  {
    id: 'p3',
    title: '코딩테스트 어떻게 준비하면 좋을까요?',
    author: '익명' + generateAnonymousId(),
    year: 18,
    createdAt: new Date(Date.now() - 432000000).toISOString(),
    views: 207,
    likes: 8,
    comments: 3,
    tags: ['취업', '코딩테스트'],
    boardId: 'ai_jobs',
    departmentId: 'ai',
    type: 'question'
  },
  {
    id: 'p3_2',
    title: 'AI 개발자 취업 후기',
    author: '익명' + generateAnonymousId(),
    year: 17,
    createdAt: new Date(Date.now() - 518400000).toISOString(),
    views: 445,
    likes: 28,
    comments: 15,
    tags: ['AI개발자', '취업후기'],
    boardId: 'ai_jobs',
    departmentId: 'ai',
    type: 'share'
  },
  
  // AI융합학부 - 장터게시판
  {
    id: 'p4',
    title: '중고 노트북 판매합니다',
    author: '익명' + generateAnonymousId(),
    year: 21,
    createdAt: new Date(Date.now() - 604800000).toISOString(),
    views: 178,
    likes: 3,
    comments: 2,
    tags: ['노트북', '중고'],
    boardId: 'ai_market',
    departmentId: 'ai',
    type: 'talk'
  },
  
  // 성서학과 - 자유게시판
  {
    id: 'p5',
    title: '성서학과 새내기 여러분 환영합니다!',
    author: '익명' + generateAnonymousId(),
    year: 20,
    createdAt: new Date(Date.now() - 691200000).toISOString(),
    views: 134,
    likes: 6,
    comments: 4,
    tags: ['환영', '새내기'],
    boardId: 'bible_free',
    departmentId: 'bible',
    type: 'share'
  },
  
  // 성서학과 - 학습게시판
  {
    id: 'p6',
    title: '성서연구 방법론에 대해 질문드려요',
    author: '익명' + generateAnonymousId(),
    year: 22,
    createdAt: new Date(Date.now() - 777600000).toISOString(),
    views: 156,
    likes: 8,
    comments: 5,
    tags: ['성서연구', '학문'],
    boardId: 'bible_study',
    departmentId: 'bible',
    type: 'question'
  },
  
  // 성서학과 - 취업/진로
  {
    id: 'p7',
    title: '신학대학원 진학 후기',
    author: '익명' + generateAnonymousId(),
    year: 17,
    createdAt: new Date(Date.now() - 864000000).toISOString(),
    views: 289,
    likes: 15,
    comments: 8,
    tags: ['진학', '신대원'],
    boardId: 'bible_jobs',
    departmentId: 'bible',
    type: 'share'
  },
  
  // 성서학과 - 장터게시판
  {
    id: 'p8',
    title: '성서학 교재 판매합니다',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 950400000).toISOString(),
    views: 98,
    likes: 2,
    comments: 1,
    tags: ['교재', '판매'],
    boardId: 'bible_market',
    departmentId: 'bible',
    type: 'talk'
  },
  
  // 간호학과 - 자유게시판
  {
    id: 'p9',
    title: '간호학과 새내기 여러분 환영합니다!',
    author: '익명' + generateAnonymousId(),
    year: 20,
    createdAt: new Date(Date.now() - 1036800000).toISOString(),
    views: 198,
    likes: 12,
    comments: 6,
    tags: ['환영', '새내기'],
    boardId: 'nursing_free',
    departmentId: 'nursing',
    type: 'share'
  },
  
  // 간호학과 - 학습게시판
  {
    id: 'p10',
    title: '실습병원 추천 부탁드립니다',
    author: '익명' + generateAnonymousId(),
    year: 21,
    createdAt: new Date(Date.now() - 1123200000).toISOString(),
    views: 167,
    likes: 9,
    comments: 5,
    tags: ['실습', '병원'],
    boardId: 'nursing_study',
    departmentId: 'nursing',
    type: 'question'
  },
  
  // 간호학과 - 취업/진로
  {
    id: 'p11',
    title: '간호사 국가고시 합격 후기',
    author: '익명' + generateAnonymousId(),
    year: 18,
    createdAt: new Date(Date.now() - 1209600000).toISOString(),
    views: 445,
    likes: 28,
    comments: 15,
    tags: ['국가고시', '합격'],
    boardId: 'nursing_jobs',
    departmentId: 'nursing',
    type: 'share'
  },
  
  // 간호학과 - 장터게시판
  {
    id: 'p12',
    title: '간호학 교재 판매합니다',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 1296000000).toISOString(),
    views: 98,
    likes: 2,
    comments: 1,
    tags: ['교재', '판매'],
    boardId: 'nursing_market',
    departmentId: 'nursing',
    type: 'talk'
  },
  
  // 영유아보육학과 - 자유게시판
  {
    id: 'p13',
    title: '영유아보육학과 새내기 여러분 환영합니다!',
    author: '익명' + generateAnonymousId(),
    year: 20,
    createdAt: new Date(Date.now() - 1382400000).toISOString(),
    views: 134,
    likes: 6,
    comments: 4,
    tags: ['환영', '새내기'],
    boardId: 'child_free',
    departmentId: 'child',
    type: 'share'
  },
  
  // 영유아보육학과 - 학습게시판
  {
    id: 'p14',
    title: '보육실습 기관 정보 공유',
    author: '익명' + generateAnonymousId(),
    year: 22,
    createdAt: new Date(Date.now() - 1468800000).toISOString(),
    views: 167,
    likes: 9,
    comments: 5,
    tags: ['보육실습', '어린이집'],
    boardId: 'child_study',
    departmentId: 'child',
    type: 'share'
  },
  
  // 영유아보육학과 - 취업/진로
  {
    id: 'p15',
    title: '보육교사 2급 자격증 관련 질문',
    author: '익명',
    year: null,
    createdAt: new Date(Date.now() - 1555200000).toISOString(),
    views: 123,
    likes: 4,
    comments: 3,
    tags: ['자격증', '보육교사'],
    boardId: 'child_jobs',
    departmentId: 'child',
    type: 'question'
  },
  
  // 영유아보육학과 - 장터게시판
  {
    id: 'p16',
    title: '보육학 교재 판매합니다',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 1641600000).toISOString(),
    views: 98,
    likes: 2,
    comments: 1,
    tags: ['교재', '판매'],
    boardId: 'child_market',
    departmentId: 'child',
    type: 'talk'
  },
  
  // 사회복지학과 - 자유게시판
  {
    id: 'p17',
    title: '사회복지학과 새내기 여러분 환영합니다!',
    author: '익명' + generateAnonymousId(),
    year: 20,
    createdAt: new Date(Date.now() - 1728000000).toISOString(),
    views: 134,
    likes: 6,
    comments: 4,
    tags: ['환영', '새내기'],
    boardId: 'social_free',
    departmentId: 'social',
    type: 'share'
  },
  
  // 사회복지학과 - 학습게시판
  {
    id: 'p18',
    title: '실습기관에서의 경험담',
    author: '익명' + generateAnonymousId(),
    year: 23,
    createdAt: new Date(Date.now() - 1814400000).toISOString(),
    views: 145,
    likes: 7,
    comments: 4,
    tags: ['실습', '경험담'],
    boardId: 'social_study',
    departmentId: 'social',
    type: 'talk'
  },
  
  // 사회복지학과 - 취업/진로
  {
    id: 'p19',
    title: '사회복지사 1급 시험 준비법',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 1900800000).toISOString(),
    views: 312,
    likes: 18,
    comments: 9,
    tags: ['사회복지사', '1급'],
    boardId: 'social_jobs',
    departmentId: 'social',
    type: 'share'
  },
  
  // 사회복지학과 - 장터게시판
  {
    id: 'p20',
    title: '사회복지학 교재 판매합니다',
    author: '익명' + generateAnonymousId(),
    year: 19,
    createdAt: new Date(Date.now() - 1987200000).toISOString(),
    views: 98,
    likes: 2,
    comments: 1,
    tags: ['교재', '판매'],
    boardId: 'social_market',
    departmentId: 'social',
    type: 'talk'
  },
  
  // 피드백 게시판 (전체 공통)
  {
    id: 'p21',
    title: '학교 식당 메뉴 개선 제안',
    author: '익명',
    year: null,
    createdAt: new Date(Date.now() - 2073600000).toISOString(),
    views: 456,
    likes: 34,
    comments: 23,
    tags: ['식당', '개선제안'],
    boardId: 'feedback',
    departmentId: null,
    type: 'question'
  },
  {
    id: 'p22',
    title: '도서관 개방시간 연장 요청',
    author: '익명' + generateAnonymousId(),
    year: 23,
    createdAt: new Date(Date.now() - 2160000000).toISOString(),
    views: 289,
    likes: 28,
    comments: 15,
    tags: ['도서관', '개방시간'],
    boardId: 'feedback',
    departmentId: null,
    type: 'question'
  }
];

const mockComments = [
  {
    id: 'c1',
    postId: 'p1',
    author: '익명' + generateAnonymousId(),
    year: 17,
    createdAt: new Date().toISOString(),
    content: '자료구조/알고리즘 기초부터, BOJ 실버→골드 단계별로 가보자고요!',
    isAnonymous: false,
    likes: 3
  },
  {
    id: 'c2',
    postId: 'p1',
    author: '익명' + generateAnonymousId(),
    year: 23,
    createdAt: new Date().toISOString(),
    content: '@선배A 감사합니다! 추천 강의 있을까요?',
    isAnonymous: false,
    likes: 1
  }
];

// ===== 유틸리티 함수 =====
function formatDate(isoString) {
  const date = new Date(isoString);
  return `${date.getFullYear()}.${(date.getMonth() + 1).toString().padStart(2, '0')}.${date.getDate().toString().padStart(2, '0')}`;
}

function formatTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return '방금 전';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
  return formatDate(isoString);
}

// ===== 게시판 전환 =====
function switchBoard(boardId) {
  currentBoard = boardId;
  
  // 활성 게시판 업데이트
  document.querySelectorAll('.board-item').forEach(item => {
    item.classList.remove('active');
  });
  document.querySelector(`[data-board-id="${boardId}"]`).classList.add('active');
  
  // 해당 학과 찾기
  const department = departments.find(dept => 
    dept.boards.some(board => board.id === boardId)
  );
  if (department) {
    currentDepartment = department.id;
    
    // 해당 학과만 열고 다른 학과들은 접기
    Object.keys(expandedDepartments).forEach(id => {
      expandedDepartments[id] = false;
    });
    expandedDepartments[department.id] = true;
    
    // 트리 다시 렌더링
    renderDepartmentTree();
  }
  
  // 게시글 필터링 및 표시
  filterAndDisplayPosts();
}

// ===== 학과 확장/축소 =====
function toggleDepartment(departmentId) {
  // 이미 열려있는 학과를 다시 클릭한 경우
  if (expandedDepartments[departmentId]) {
    // 해당 학과만 접기
    expandedDepartments[departmentId] = false;
  } else {
    // 다른 학과들은 모두 접기
    Object.keys(expandedDepartments).forEach(id => {
      expandedDepartments[id] = false;
    });
    
    // 클릭한 학과만 열기
    expandedDepartments[departmentId] = true;
  }
  
  renderDepartmentTree();
}

// ===== 학과 트리 렌더링 =====
function renderDepartmentTree() {
  const treeContainer = document.getElementById('departmentTree');
  
  treeContainer.innerHTML = departments.map(department => `
    <div class="department-item">
      <div class="department-header" onclick="toggleDepartment('${department.id}')">
        <span class="department-name">
          <span class="department-icon">${department.icon}</span>
          <span class="department-icon-text">${department.iconText}</span>
          ${department.name}
        </span>
        <svg class="department-arrow ${expandedDepartments[department.id] ? 'expanded' : ''}" 
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </div>
      <div class="department-boards ${expandedDepartments[department.id] ? 'expanded' : ''}">
        ${department.boards.map(board => `
          <div class="board-item ${currentBoard === board.id ? 'active' : ''}" 
               data-board-id="${board.id}" 
               onclick="switchBoard('${board.id}')">
            ${board.name}
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ===== 게시글 필터링 및 표시 =====
function filterAndDisplayPosts() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase();
  const sortBy = document.getElementById('sortSelect').value;
  
  let filteredPosts = posts.filter(post => {
    // 게시판 필터 (새로운 boardId 구조에 맞게)
    if (post.boardId !== currentBoard) return false;
    
    // 검색 필터
    if (searchTerm) {
      const matchesTitle = post.title.toLowerCase().includes(searchTerm);
      const matchesTags = post.tags && post.tags.some(tag => tag.toLowerCase().includes(searchTerm));
      if (!matchesTitle && !matchesTags) return false;
    }
    
    return true;
  });
  
  // 정렬
  filteredPosts.sort((a, b) => {
    switch (sortBy) {
      case 'popular':
        return b.likes - a.likes;
      case 'views':
        return b.views - a.views;
      case 'latest':
      default:
        return new Date(b.createdAt) - new Date(a.createdAt);
    }
  });
  
  displayPosts(filteredPosts);
}

// ===== 게시글 표시 =====
function displayPosts(postsToShow) {
  const postsList = document.getElementById('postsList');
  const emptyState = document.getElementById('emptyState');
  const loadingState = document.getElementById('loadingState');
  
  // 로딩 상태 숨기기
  loadingState.style.display = 'none';
  
  if (postsToShow.length === 0) {
    postsList.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }
  
  emptyState.style.display = 'none';
  
  postsList.innerHTML = postsToShow.map(post => `
    <div class="post-card" data-post-id="${post.id}">
      <div class="post-content">
        <div class="post-header">
          <div class="post-info">
            <div class="post-badges">
              ${post.tags ? post.tags.map(tag => `<span class="badge badge-secondary">#${tag}</span>`).join('') : ''}
              <span class="badge badge-outline">
                ${post.type === 'question' ? '질문' : post.type === 'share' ? '정보' : '게시글'}
              </span>
              ${post.departmentId ? `<span class="badge badge-outline">${departments.find(d => d.id === post.departmentId)?.name || post.departmentId}</span>` : ''}
            </div>
            <div class="post-title" onclick="viewPost('${post.id}')">${post.title}</div>
            <div class="post-meta">${post.author} · ${getYearDisplay(post.year)} · ${formatTime(post.createdAt)}</div>
          </div>
          <div class="post-stats">
            <div class="stat-item">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              ${post.views}
            </div>
            <div class="stat-item like-btn ${isLiked(post.id) ? 'liked' : ''}" onclick="toggleLike('${post.id}'); event.stopPropagation();">
              <svg width="16" height="16" fill="${isLiked(post.id) ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
              </svg>
              ${post.likes}
            </div>
            <div class="stat-item">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              ${post.comments}
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

// ===== 게시글 상세보기 =====
function viewPost(postId) {
  const post = posts.find(p => p.id === postId);
  if (!post) return;
  
  // 현재 게시글 ID 저장 (좋아요 업데이트용)
  window.currentPostId = postId;
  
  // 조회수 증가
  post.views += 1;
  
  // 목록 화면 숨기기
  document.getElementById('postsList').style.display = 'none';
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('loadingState').style.display = 'none';
  
  // 상세 화면 표시
  document.getElementById('postDetailView').style.display = 'block';
  
  // 해당 게시글의 댓글들 가져오기
  const postComments = comments.filter(c => c.postId === postId);
  
  // 상세 화면 렌더링
  renderPostDetail(post, postComments);
}

// ===== 게시글 상세 화면 렌더링 =====
function renderPostDetail(post, postComments) {
  const detailView = document.getElementById('postDetailView');
  
  // 학과 정보 가져오기
  const department = departments.find(d => d.id === post.departmentId);
  
  detailView.innerHTML = `
    <button class="detail-back-btn" onclick="backToList()">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
      </svg>
      목록으로
    </button>
    
    <div class="detail-content">
      <div class="detail-badges">
        ${post.tags ? post.tags.map(tag => `<span class="badge badge-secondary">#${tag}</span>`).join('') : ''}
        <span class="badge badge-outline">
          ${post.type === 'question' ? '질문' : post.type === 'share' ? '정보' : '게시글'}
        </span>
        ${department ? `<span class="badge badge-outline">${department.name}</span>` : ''}
      </div>
      
      <h1 class="detail-title">${post.title}</h1>
      
      <div class="detail-meta">${post.author} · ${getYearDisplay(post.year)} · ${formatTime(post.createdAt)}</div>
      
      <div class="detail-stats">
        <div class="stat-item like-btn ${isLiked(post.id) ? 'liked' : ''}" onclick="toggleLike('${post.id}')">
          <svg width="16" height="16" fill="${isLiked(post.id) ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
          </svg>
          ${post.likes}
        </div>
        <div class="stat-item">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
          </svg>
          ${post.views}
        </div>
        <div class="stat-item">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          ${post.comments}
        </div>
      </div>
      
      <div class="detail-body">
        <p>본 시안은 선후배가 편하게 소통하도록 구성한 게시판 상세 화면입니다. 불필요한 요소는 숨기고 <strong>읽기와 답변</strong>에 집중했어요.</p>
        <ul>
          <li>@멘션과 #태그 입력 안내를 에디터 placeholder로 제공합니다.</li>
          <li>익명 토글로 편안하게 질문/답변을 남길 수 있습니다.</li>
        </ul>
        <p>실제 게시글 내용이 여기에 표시됩니다. 사용자가 작성한 본문 내용이 들어갈 예정입니다.</p>
      </div>
      
      <div class="detail-comments-section">
        <div class="comments-header">댓글 ${postComments.length}</div>
        
        <div class="comments-list">
          ${postComments.map(comment => `
            <div class="comment-item" data-comment-id="${comment.id}">
              <div class="comment-meta">${comment.author} · ${getYearDisplay(comment.year)} · ${formatTime(comment.createdAt)}</div>
              <div class="comment-content">${comment.content}</div>
              <div class="comment-actions">
                <button class="comment-like-btn ${isCommentLiked(comment.id) ? 'liked' : ''}" onclick="toggleCommentLike('${comment.id}')">
                  <svg width="14" height="14" fill="${isCommentLiked(comment.id) ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                  </svg>
                  ${comment.likes}
                </button>
              </div>
            </div>
          `).join('')}
        </div>
        
        <form class="comment-form" onsubmit="submitDetailComment(event, '${post.id}')">
          <input type="text" class="comment-input" placeholder="@멘션, #태그와 함께 댓글을 입력하세요" required />
          <label class="comment-anonymous">
            <input type="checkbox" class="comment-anonymous-checkbox" />
            <span class="toggle-switch"></span>
            익명
          </label>
          <button type="submit" class="comment-send-btn">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
            전송
          </button>
        </form>
      </div>
    </div>
  `;
  
  // 익명 토글 이벤트 추가
  const anonymousCheckbox = detailView.querySelector('.comment-anonymous-checkbox');
  if (anonymousCheckbox) {
    anonymousCheckbox.addEventListener('change', function() {
      const toggle = this.nextElementSibling;
      if (this.checked) {
        toggle.classList.add('active');
      } else {
        toggle.classList.remove('active');
      }
    });
  }
}

// ===== 목록으로 돌아가기 =====
function backToList() {
  document.getElementById('postDetailView').style.display = 'none';
  document.getElementById('postsList').style.display = 'block';
  filterAndDisplayPosts();
}

// ===== 상세 화면 댓글 작성 =====
function submitDetailComment(event, postId) {
  event.preventDefault();
  
  const form = event.target;
  const input = form.querySelector('.comment-input');
  const anonymousCheckbox = form.querySelector('.comment-anonymous-checkbox');
  
  const content = input.value.trim();
  if (!content) return;
  
  const newComment = {
    id: 'c' + Date.now(),
    postId: postId,
    author: anonymousCheckbox.checked ? '익명' + generateAnonymousId() : '익명' + generateAnonymousId(),
    year: anonymousCheckbox.checked ? null : 24,
    createdAt: new Date().toISOString(),
    content: content,
    isAnonymous: anonymousCheckbox.checked,
    likes: 0
  };
  
  comments.push(newComment);
  
  // 해당 게시글의 댓글 수 증가
  const post = posts.find(p => p.id === postId);
  if (post) {
    post.comments++;
  }
  
  // 입력 필드 초기화
  input.value = '';
  anonymousCheckbox.checked = false;
  const toggle = anonymousCheckbox.nextElementSibling;
  toggle.classList.remove('active');
  
  // 상세 화면 새로고침
  const postComments = comments.filter(c => c.postId === postId);
  renderPostDetail(post, postComments);
  
  console.log('상세 화면 댓글 작성됨:', newComment);
}


// ===== 글쓰기 모달 =====
function showWriteModal() {
  document.getElementById('writeModal').style.display = 'flex';
  document.getElementById('postTitle').focus();
  
  // 현재 게시판에 맞는 학과 자동 선택
  const department = departments.find(dept => 
    dept.boards.some(board => board.id === currentBoard)
  );
  if (department) {
    document.getElementById('postDepartment').value = department.id;
  }
  
}

function hideWriteModal() {
  document.getElementById('writeModal').style.display = 'none';
  document.getElementById('writeForm').reset();
  document.getElementById('tagsContainer').innerHTML = '';
  
}


// ===== 댓글 모달 =====
function showCommentModal(postId) {
  document.getElementById('commentModal').style.display = 'flex';
  loadComments(postId);
}

function hideCommentModal() {
  document.getElementById('commentModal').style.display = 'none';
  document.getElementById('commentForm').reset();
}

function loadComments(postId) {
  const postComments = comments.filter(c => c.postId === postId);
  const commentsList = document.getElementById('commentsList');
  
  commentsList.innerHTML = postComments.map(comment => `
    <div class="comment-item">
      <div class="comment-meta">${comment.author} · ${getYearDisplay(comment.year)} · ${formatTime(comment.createdAt)}</div>
      <div class="comment-content">${comment.content}</div>
    </div>
  `).join('');
}

// ===== 태그 관리 =====
function addTag(tagInput) {
  const input = document.getElementById(tagInput);
  const container = document.getElementById('tagsContainer');
  
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const tag = input.value.trim().replace(/^#/, '');
      if (tag && !container.querySelector(`[data-tag="${tag}"]`)) {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag-item';
        tagElement.setAttribute('data-tag', tag);
        tagElement.innerHTML = `
          #${tag}
          <button type="button" class="remove-tag" onclick="removeTag('${tag}')">×</button>
        `;
        container.appendChild(tagElement);
      }
      input.value = '';
    }
  });
}

function removeTag(tag) {
  const tagElement = document.querySelector(`[data-tag="${tag}"]`);
  if (tagElement) {
    tagElement.remove();
  }
}

// ===== 폼 제출 =====
function submitPost(event) {
  event.preventDefault();
  
  const form = event.target;
  const title = form.postTitle.value.trim();
  const content = form.postContent.value.trim();
  const type = form.postType.value;
  const department = form.postDepartment.value;
  const isAnonymous = form.postAnonymous.checked;
  
  if (!title || !content) {
    alert('제목과 내용을 모두 입력해주세요.');
    return;
  }
  
  const tags = Array.from(document.querySelectorAll('#tagsContainer .tag-item')).map(item => 
    item.getAttribute('data-tag')
  );
  
  const newPost = {
    id: 'p' + Date.now(),
    title: title,
    author: '익명' + generateAnonymousId(),
    year: isAnonymous ? null : 24,
    createdAt: new Date().toISOString(),
    views: 0,
    likes: 0,
    comments: 0,
    tags: tags,
    boardId: currentBoard,
    departmentId: department || null,
    type: type
  };
  
  posts.unshift(newPost);
  
  hideWriteModal();
  filterAndDisplayPosts();
  
  console.log('게시글 작성됨:', newPost);
}

// ===== 이벤트 리스너 =====
document.addEventListener('DOMContentLoaded', function() {
  // 목업 데이터 초기화
  posts = [...mockPosts];
  comments = [...mockComments];
  
  // 마이페이지에서 온 경우 특정 게시글로 이동
  const urlParams = new URLSearchParams(window.location.search);
  const postId = urlParams.get('postId');
  const source = urlParams.get('source');
  const type = urlParams.get('type');
  const commentId = urlParams.get('commentId');
  
  if (postId && source === 'mypage') {
    // 해당 게시글 찾기
    const post = posts.find(p => p.id === postId);
    if (post) {
      viewPost(postId);
      
      // 댓글 좋아요인 경우 해당 댓글로 스크롤
      if (type === 'commentLike' && commentId) {
        setTimeout(() => {
          const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
          if (commentElement) {
            commentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            commentElement.style.backgroundColor = '#fff3cd';
            setTimeout(() => {
              commentElement.style.backgroundColor = '';
            }, 3000);
          }
        }, 500);
      }
    }
  }
  
  // 학과 트리 렌더링
  renderDepartmentTree();
  
  // 검색 및 정렬 이벤트
  document.getElementById('searchInput').addEventListener('input', filterAndDisplayPosts);
  document.getElementById('sortSelect').addEventListener('change', filterAndDisplayPosts);
  
  // 태그 입력 이벤트
  addTag('tagInput');
  
  // 폼 제출 이벤트
  document.getElementById('writeForm').addEventListener('submit', submitPost);
  
  // 익명 토글 이벤트
  document.querySelectorAll('.anonymous-toggle input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const toggle = this.nextElementSibling;
      if (this.checked) {
        toggle.classList.add('active');
      } else {
        toggle.classList.remove('active');
      }
    });
  });
  
  // 모달 외부 클릭 시 닫기
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.style.display = 'none';
      }
    });
  });
  
  // ESC 키로 모달 닫기
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
      });
    }
  });
  
  // 초기 게시글 표시 (모든 학과가 닫혀있으므로 게시글을 표시하지 않음)
  // filterAndDisplayPosts();
  
  // 모바일 메뉴 토글
  const menuBtn = document.getElementById('menuBtn');
  const mobileNav = document.getElementById('mobileNav');
  
  if (menuBtn && mobileNav) {
    menuBtn.addEventListener('click', function() {
      mobileNav.classList.toggle('hidden');
    });
  }
  
  // 년도 설정
  document.getElementById('year').textContent = new Date().getFullYear();
});
