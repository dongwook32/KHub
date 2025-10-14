// KBU Hub 게시판 JavaScript

// ===== 전역 변수 =====
let currentBoard = 'free_board'; // 기본값을 자유게시판으로 설정
let currentDepartment = 'free';
let posts = [];
let comments = [];
let expandedDepartments = { 'free': true }; // 자유게시판은 기본으로 열린 상태

// ===== 접근 권한 관리 =====
// 사용자 학과 정보 (Flask에서 전달받음)
const userDepartment = window.userDepartment || 'free';

// 학과별 접근 가능한 게시판 매핑
function getAccessibleDepartments(userDept) {
  // 모든 사용자는 자유게시판 접근 가능
  const accessible = ['free'];
  
  // 본인 학과 추가
  if (userDept && userDept !== 'free' && userDept !== 'unknown') {
    accessible.push(userDept);
  }
  
  return accessible;
}

// 게시판 접근 권한 체크
function canAccessDepartment(departmentId) {
  const accessible = getAccessibleDepartments(userDepartment);
  return accessible.includes(departmentId);
}

// ===== 익명 번호 관리 =====
// 게시글별 익명 번호 매핑: { postId: { studentId: anonymousNumber, ... }, ... }
const postAnonymousMap = {};

// 게시글별로 사용자에게 일관된 익명 번호를 부여
function getAnonymousIdForPost(postId, studentId) {
  // 해당 게시글의 매핑이 없으면 생성
  if (!postAnonymousMap[postId]) {
    postAnonymousMap[postId] = {
      counter: 1,
      userMap: {}
    };
  }
  
  // 이미 이 사용자에게 번호가 부여되었는지 확인
  if (!postAnonymousMap[postId].userMap[studentId]) {
    // 새 번호 부여
    postAnonymousMap[postId].userMap[studentId] = postAnonymousMap[postId].counter;
    postAnonymousMap[postId].counter++;
  }
  
  return postAnonymousMap[postId].userMap[studentId];
}

// 기존 게시글과 댓글에서 익명 번호 매핑 재구성
function rebuildAnonymousMap(posts, comments) {
  posts.forEach(post => {
    if (post.authorStudentId) {
      // 게시글 작성자 매핑 재구성
      getAnonymousIdForPost(post.id, post.authorStudentId);
    }
  });
  
  comments.forEach(comment => {
    if (comment.authorStudentId) {
      // 댓글 작성자 매핑 재구성
      getAnonymousIdForPost(comment.postId, comment.authorStudentId);
    }
  });
}

// 하위 호환성을 위한 함수 (사용하지 않음)
function generateAnonymousId() {
  return Math.floor(Math.random() * 1000) + 1;
}

// ===== 좋아요 관리 =====
let likedPosts = new Set(); // 좋아요한 게시글 ID 저장
let likedComments = new Set(); // 좋아요한 댓글 ID 저장

async function toggleLike(postId) {
  const post = posts.find(p => p.id === postId);
  if (!post) return;
  
  const currentUser = localStorage.getItem('currentUser');
  
  if (likedPosts.has(postId)) {
    // 좋아요 취소
    likedPosts.delete(postId);
    post.likes = Math.max(0, post.likes - 1);
    
    // localStorage에서 제거
    if (currentUser) {
      try {
        const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
        activity.likes = activity.likes.filter(like => like.postId !== postId);
        localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
      } catch (e) {
        console.error('좋아요 기록 제거 실패:', e);
      }
    }
  } else {
    // 좋아요 추가
    likedPosts.add(postId);
    post.likes += 1;
    
    // localStorage에 추가
    if (currentUser) {
      try {
        const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
        activity.likes.unshift({
          id: Date.now(),
          postId: postId,
          postTitle: post.title,
          postAuthor: post.author,
          date: new Date().toISOString()
        });
        localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
      } catch (e) {
        console.error('좋아요 기록 저장 실패:', e);
      }
    }
  }
  
  // 서버에 좋아요 수 저장
  try {
    await fetch(`/api/board-posts/${postId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ likes: post.likes })
    });
  } catch (error) {
    console.error('좋아요 서버 저장 오류:', error);
  }
  
  // 게시글 정보 저장 (좋아요 수 변경)
  savePostsToLocalStorage();
  
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

async function toggleCommentLike(commentId) {
  const comment = comments.find(c => c.id === commentId);
  if (!comment) return;
  
  const currentUser = localStorage.getItem('currentUser');
  
  if (likedComments.has(commentId)) {
    // 좋아요 취소
    likedComments.delete(commentId);
    comment.likes = Math.max(0, comment.likes - 1);
    
    // 댓글 정보 저장
    saveCommentsToLocalStorage();
    
    // localStorage에서 제거
    if (currentUser) {
      try {
        const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
        activity.commentLikes = activity.commentLikes.filter(like => like.commentId !== commentId);
        localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
      } catch (e) {
        console.error('댓글 좋아요 기록 제거 실패:', e);
      }
    }
  } else {
    // 좋아요 추가
    likedComments.add(commentId);
    comment.likes += 1;
    
    // 댓글 정보 저장
    saveCommentsToLocalStorage();
    
    // localStorage에 추가
    if (currentUser) {
      try {
        const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
        activity.commentLikes.unshift({
          id: Date.now(),
          commentId: commentId,
          commentContent: comment.content,
          commentAuthor: comment.author,
          postId: comment.postId,
          date: new Date().toISOString()
        });
        localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
      } catch (e) {
        console.error('댓글 좋아요 기록 저장 실패:', e);
      }
    }
  }
  
  // 서버에 댓글 좋아요 수 저장
  try {
    await fetch(`/api/board-comments/${commentId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ likes: comment.likes })
    });
  } catch (error) {
    console.error('댓글 좋아요 서버 저장 오류:', error);
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
function getYearDisplay(year, status) {
  if (!year) return '익명';
  
  // year가 문자열 형태일 경우 (예: "22학번") 숫자만 추출
  let yearNum = year;
  if (typeof year === 'string') {
    yearNum = parseInt(year.replace(/[^0-9]/g, ''));
  }
  
  // status가 전달되면 사용, 아니면 학년으로 계산
  let statusText = '';
  if (status) {
    statusText = status;
  } else {
    const currentYear = new Date().getFullYear();
    const admissionYear = 2000 + yearNum;
    const grade = currentYear - admissionYear + 1;
    
    if (grade <= 0) statusText = '신입생';
    else if (grade >= 5) statusText = '졸업생';
    else statusText = '재학생';
  }
  
  return `${yearNum}학번 ${statusText}`;
}

// ===== 학과 및 게시판 정보 =====
const departments = [
  { 
    id: 'free', 
    name: '자유게시판', 
    icon: '💬',
    iconText: '[자유]',
    boards: [
      { id: 'free_board', name: '전체 자유게시판' },
      { id: 'free_study', name: '학업게시판' },
      { id: 'free_market', name: '장터게시판' }
    ]
  },
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
const mockPosts = [];

const mockComments = [];

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
  // 해당 게시판이 속한 학과 찾기
  const department = departments.find(dept => 
    dept.boards.some(board => board.id === boardId)
  );
  
  // 접근 권한 체크
  if (department && !canAccessDepartment(department.id)) {
    alert('본인 학과가 아닙니다. 접근이 불가능합니다.');
    return;
  }
  
  currentBoard = boardId;
  
  // 활성 게시판 업데이트
  document.querySelectorAll('.board-item').forEach(item => {
    item.classList.remove('active');
  });
  const boardElement = document.querySelector(`[data-board-id="${boardId}"]`);
  if (boardElement) {
    boardElement.classList.add('active');
  }
  
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
  
  treeContainer.innerHTML = departments.map(department => {
    const hasAccess = canAccessDepartment(department.id);
    
    return `
    <div class="department-item ${!hasAccess ? 'department-locked' : ''}">
      <div class="department-header" onclick="${hasAccess ? `toggleDepartment('${department.id}')` : `alert('본인 학과가 아닙니다. 접근이 불가능합니다.')`}">
        <span class="department-name">
          <span class="department-icon">${department.icon}</span>
          <span class="department-icon-text">${department.iconText}</span>
          ${department.name}
          ${!hasAccess ? '<span style="margin-left:8px;font-size:0.75rem;opacity:0.5;">🔒</span>' : ''}
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
  `;
  }).join('');
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
            <div class="post-meta">${post.author} · ${getYearDisplay(post.year, post.status)} · ${formatTime(post.createdAt)}</div>
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

// ===== 게시글 수정 모달 열기 =====
function openEditModal(postId) {
  const post = posts.find(p => p.id === postId);
  if (!post) {
    alert('게시글을 찾을 수 없습니다.');
    return;
  }
  
  // 수정 폼에 기존 데이터 채우기
  document.getElementById('editPostId').value = post.id;
  document.getElementById('editPostTitle').value = post.title;
  document.getElementById('editPostContent').value = post.content;
  
  // 기존 태그 표시
  const editTagsContainer = document.getElementById('editTagsContainer');
  editTagsContainer.innerHTML = '';
  if (post.tags && post.tags.length > 0) {
    post.tags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.innerHTML = `
        #${tag}
        <button type="button" onclick="removeEditTag('${tag}')">&times;</button>
      `;
      editTagsContainer.appendChild(tagSpan);
    });
  }
  
  // 수정 태그 입력 이벤트 추가
  addTag('editTagInput');
  
  // 모달 표시
  document.getElementById('editModal').style.display = 'flex';
}

// ===== 수정 모달 닫기 =====
function hideEditModal() {
  document.getElementById('editModal').style.display = 'none';
  document.getElementById('editForm').reset();
  document.getElementById('editTagsContainer').innerHTML = '';
}

// ===== 수정 태그 제거 =====
function removeEditTag(tagToRemove) {
  const editTagsContainer = document.getElementById('editTagsContainer');
  const tags = Array.from(editTagsContainer.querySelectorAll('.tag'));
  tags.forEach(tag => {
    if (tag.textContent.trim().replace('×', '').replace('#', '') === tagToRemove) {
      tag.remove();
    }
  });
}

// ===== 게시글 수정 제출 =====
async function submitEdit(event) {
  event.preventDefault();
  
  const postId = document.getElementById('editPostId').value;
  const title = document.getElementById('editPostTitle').value.trim();
  const content = document.getElementById('editPostContent').value.trim();
  
  // 태그 수집
  const editTagsContainer = document.getElementById('editTagsContainer');
  const tags = Array.from(editTagsContainer.querySelectorAll('.tag')).map(tag => {
    return tag.textContent.trim().replace('×', '').replace('#', '');
  });
  
  if (!title || !content) {
    alert('제목과 내용을 입력해주세요.');
    return;
  }
  
  try {
    // 서버에 수정 요청
    const response = await fetch(`/api/board-posts/${postId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: title,
        content: content,
        tags: tags
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 서버에서 게시글 다시 로드
      posts = await loadPostsFromServer();
      comments = await loadCommentsFromServer();
      
      // 익명 번호 매핑 재구성
      rebuildAnonymousMap(posts, comments);
      
      // localStorage 활동 기록 업데이트
      const currentUser = localStorage.getItem('currentUser');
      if (currentUser) {
        try {
          const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
          
          // 내가 작성한 글 목록에서 업데이트
          const postIndex = activity.posts.findIndex(p => p.id === postId);
          if (postIndex !== -1) {
            activity.posts[postIndex].title = title;
            activity.posts[postIndex].content = content;
            activity.posts[postIndex].tags = tags;
          }
          
          localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
        } catch (e) {
          console.error('활동 기록 업데이트 실패:', e);
        }
      }
      
      // 모달 닫기
      hideEditModal();
      
      // 수정된 게시글 다시 표시
      const post = posts.find(p => p.id === postId);
      if (post) {
        const postComments = comments.filter(c => c.postId === postId);
        renderPostDetail(post, postComments);
      }
      
      alert('게시글이 수정되었습니다.');
    } else {
      alert(result.message || '게시글 수정 중 오류가 발생했습니다.');
    }
  } catch (error) {
    console.error('게시글 수정 오류:', error);
    alert('게시글 수정 중 오류가 발생했습니다.');
  }
}

// ===== 게시글 삭제 =====
async function deletePost(postId) {
  if (!confirm('정말 이 게시글을 삭제하시겠습니까?')) {
    return;
  }
  
  // 게시글 찾기
  const postIndex = posts.findIndex(p => p.id === postId);
  if (postIndex === -1) {
    alert('게시글을 찾을 수 없습니다.');
    return;
  }
  
  try {
    // 서버에서 게시글 삭제
    const response = await fetch(`/api/board-posts/${postId}`, {
      method: 'DELETE'
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 서버에서 게시글과 댓글 다시 로드
      posts = await loadPostsFromServer();
      comments = await loadCommentsFromServer();
      
      // localStorage에서 삭제 (마이페이지 활동 기록)
      const currentUser = localStorage.getItem('currentUser');
      if (currentUser) {
        try {
          const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
          
          // 내가 작성한 글 목록에서 삭제
          activity.posts = activity.posts.filter(p => p.id !== postId);
          
          // 다른 사람이 좋아요한 글 목록에서도 삭제
          activity.likes = activity.likes.filter(l => l.postId !== postId);
          
          // 댓글도 삭제
          activity.comments = activity.comments.filter(c => c.postId !== postId);
          
          localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
        } catch (e) {
          console.error('활동 기록 삭제 실패:', e);
        }
      }
      
      // 목록으로 돌아가기
      backToList();
      
      alert('게시글이 삭제되었습니다.');
    } else {
      alert(result.message || '게시글 삭제 중 오류가 발생했습니다.');
    }
  } catch (error) {
    console.error('게시글 삭제 오류:', error);
    alert('게시글 삭제 중 오류가 발생했습니다.');
  }
}

// ===== 댓글 삭제 =====
async function deleteComment(commentId, postId) {
  if (!confirm('정말 이 댓글을 삭제하시겠습니까?')) {
    return;
  }
  
  try {
    // 서버에서 댓글 삭제
    const response = await fetch(`/api/board-comments/${commentId}`, {
      method: 'DELETE'
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 서버에서 게시글과 댓글 다시 로드
      posts = await loadPostsFromServer();
      comments = await loadCommentsFromServer();
      
      // 익명 번호 매핑 재구성
      rebuildAnonymousMap(posts, comments);
      
      // localStorage에서 삭제 (마이페이지 활동 기록)
      const currentUser = localStorage.getItem('currentUser');
      if (currentUser) {
        try {
          const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
          
          // 내가 작성한 댓글 목록에서 삭제
          activity.comments = activity.comments.filter(c => c.id !== commentId);
          
          // 댓글 좋아요 목록에서도 삭제
          activity.commentLikes = activity.commentLikes.filter(l => l.commentId !== commentId);
          
          localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
        } catch (e) {
          console.error('활동 기록 삭제 실패:', e);
        }
      }
      
      // 상세 화면 새로고침
      const post = posts.find(p => p.id === postId);
      if (post) {
        const postComments = comments.filter(c => c.postId === postId);
        renderPostDetail(post, postComments);
      }
      
      alert('댓글이 삭제되었습니다.');
    } else {
      alert(result.message || '댓글 삭제 중 오류가 발생했습니다.');
    }
  } catch (error) {
    console.error('댓글 삭제 오류:', error);
    alert('댓글 삭제 중 오류가 발생했습니다.');
  }
}

// ===== 게시글 상세 화면 렌더링 =====
function renderPostDetail(post, postComments) {
  const detailView = document.getElementById('postDetailView');
  
  // 학과 정보 가져오기
  const department = departments.find(d => d.id === post.departmentId);
  
  // 현재 사용자가 작성자인지 확인
  const userProfile = JSON.parse(localStorage.getItem('userProfile') || 'null');
  const isAuthor = userProfile && post.authorStudentId && userProfile.studentId === post.authorStudentId;
  
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
      
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
        <h1 class="detail-title" style="flex: 1; margin: 0;">${post.title}</h1>
        ${isAuthor ? `
        <div style="display: flex; gap: 8px;">
          <button onclick="openEditModal('${post.id}')" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; white-space: nowrap; transition: all 0.3s ease;" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            수정
          </button>
          <button onclick="deletePost('${post.id}')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; white-space: nowrap; transition: all 0.3s ease;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
            삭제
          </button>
        </div>
        ` : ''}
      </div>
      
      <div class="detail-meta">
        ${post.author} · ${getYearDisplay(post.year, post.status)} · ${formatTime(post.createdAt)}
        ${post.updatedAt ? `<span style="color: #6B7280; font-size: 12px;"> (수정됨)</span>` : ''}
      </div>
      
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
        ${post.content ? post.content.split('\n').map(line => `<p>${line || '&nbsp;'}</p>`).join('') : '<p>내용이 없습니다.</p>'}
      </div>
      
      <div class="detail-comments-section">
        <div class="comments-header">댓글 ${postComments.length}</div>
        
        <div class="comments-list">
          ${postComments.map(comment => {
            // 현재 사용자가 댓글 작성자인지 확인
            const isCommentAuthor = userProfile && comment.authorStudentId && userProfile.studentId === comment.authorStudentId;
            
            return `
            <div class="comment-item" data-comment-id="${comment.id}">
              <div class="comment-meta" style="display: flex; justify-content: space-between; align-items: center;">
                <span>${comment.author} · ${getYearDisplay(comment.year, comment.status)} · ${formatTime(comment.createdAt)}</span>
                ${isCommentAuthor ? `
                  <button onclick="deleteComment('${comment.id}', '${post.id}')" style="padding: 4px 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s ease;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">
                    삭제
                  </button>
                ` : ''}
              </div>
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
            `;
          }).join('')}
        </div>
        
        <form class="comment-form" onsubmit="submitDetailComment(event, '${post.id}')">
          <input type="text" class="comment-input" placeholder="@멘션, #태그와 함께 댓글을 입력하세요" required />
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
}

// ===== 목록으로 돌아가기 =====
function backToList() {
  document.getElementById('postDetailView').style.display = 'none';
  document.getElementById('postsList').style.display = 'block';
  filterAndDisplayPosts();
}

// ===== 상세 화면 댓글 작성 =====
async function submitDetailComment(event, postId) {
  event.preventDefault();
  
  const form = event.target;
  const input = form.querySelector('.comment-input');
  
  const content = input.value.trim();
  if (!content) return;
  
  // 사용자 정보 가져오기
  const userProfile = JSON.parse(localStorage.getItem('userProfile') || 'null');
  const anonProfile = JSON.parse(localStorage.getItem('anonProfile') || 'null');
  
  // 학번에서 입학년도 추출 (항상 익명 처리)
  let yearDisplay = null;
  let statusDisplay = null;
  
  if (anonProfile && anonProfile.year) {
    // 익명 프로필에서 학번 정보 가져오기
    yearDisplay = anonProfile.year.replace(/[^0-9]/g, ''); // "22학번" -> "22"
    statusDisplay = null; // 익명일 때는 상태 표시 안함
  }
  
  // 현재 사용자의 학번
  const currentUserStudentId = userProfile ? userProfile.studentId : null;
  
  // 게시글별로 일관된 익명 번호 부여
  const anonymousId = currentUserStudentId ? getAnonymousIdForPost(postId, currentUserStudentId) : generateAnonymousId();
  
  const newComment = {
    id: 'c' + Date.now(),
    postId: postId,
    author: '익명' + anonymousId,
    authorStudentId: currentUserStudentId, // 작성자 학번 저장
    year: yearDisplay ? parseInt(yearDisplay) : null,
    status: statusDisplay,
    createdAt: new Date().toISOString(),
    content: content,
    isAnonymous: true, // 항상 익명
    likes: 0
  };
  
  try {
    // 서버에 댓글 저장
    const response = await fetch('/api/board-comments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newComment)
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 서버에서 게시글과 댓글 다시 로드
      comments = await loadCommentsFromServer();
      
      // 해당 게시글의 댓글 수 증가
      const post = posts.find(p => p.id === postId);
      if (post) {
        post.comments++;
        
        // 서버에 게시글 댓글 수 업데이트
        try {
          await fetch(`/api/board-posts/${postId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ comments: post.comments })
          });
        } catch (error) {
          console.error('게시글 댓글 수 업데이트 오류:', error);
        }
      }
      
      // 마이페이지 활동 기록에 추가
      const currentUser = localStorage.getItem('currentUser');
      if (currentUser) {
        try {
          const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
          
          activity.comments.unshift({
            id: newComment.id,
            content: newComment.content,
            postTitle: post ? post.title : '삭제된 게시글',
            postId: postId,
            date: newComment.createdAt
          });
          
          localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
        } catch (e) {
          console.error('활동 기록 저장 실패:', e);
        }
      }
      
      // 입력 필드 초기화
      input.value = '';
      
      // 상세 화면 새로고침
      const postComments = comments.filter(c => c.postId === postId);
      renderPostDetail(post, postComments);
      
      console.log('상세 화면 댓글 작성됨:', newComment);
    } else {
      alert(result.message || '댓글 작성 중 오류가 발생했습니다.');
    }
  } catch (error) {
    console.error('댓글 작성 오류:', error);
    alert('댓글 작성 중 오류가 발생했습니다.');
  }
}

// ===== 댓글 저장/로드 함수 =====
function saveCommentsToLocalStorage() {
  // 서버 기반으로 변경되어 localStorage 저장 비활성화
  // 댓글은 서버에만 저장됩니다
  console.log('댓글은 서버에 저장됩니다.');
}

async function loadCommentsFromServer() {
  try {
    const response = await fetch('/api/board-comments');
    const result = await response.json();
    
    if (result.success && result.comments) {
      console.log('서버에서 댓글 로드됨:', result.comments.length + '개');
      // 서버 댓글과 mockComments 병합
      return [...result.comments, ...mockComments];
    }
  } catch (e) {
    console.error('서버에서 댓글 로드 실패:', e);
  }
  return [...mockComments];
}

function loadCommentsFromLocalStorage() {
  try {
    const savedComments = localStorage.getItem('boardComments');
    if (savedComments) {
      const userComments = JSON.parse(savedComments);
      console.log('로컬 댓글 로드됨:', userComments.length + '개');
      // mockComments와 병합 (사용자 댓글을 앞에 배치)
      return [...userComments, ...mockComments];
    }
  } catch (e) {
    console.error('댓글 로드 실패:', e);
  }
  return [...mockComments];
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

// 폼 제출 중 플래그
let isSubmitting = false;

// ===== 폼 제출 =====
async function submitPost(event) {
  event.preventDefault();
  
  // 중복 제출 방지
  if (isSubmitting) {
    console.log('이미 제출 중입니다.');
    return;
  }
  
  const form = event.target;
  const title = form.postTitle.value.trim();
  const content = form.postContent.value.trim();
  const type = form.postType.value;
  const department = form.postDepartment.value;
  const isAnonymous = true; // 항상 익명으로 처리
  
  if (!title || !content) {
    alert('제목과 내용을 모두 입력해주세요.');
    return;
  }
  
  // 제출 시작
  isSubmitting = true;
  
  const tags = Array.from(document.querySelectorAll('#tagsContainer .tag-item')).map(item => 
    item.getAttribute('data-tag')
  );
  
  // 학과 정보 가져오기
  const dept = departments.find(d => d.id === department);
  const categoryName = dept ? dept.name : '자유게시판';
  
  // 사용자 정보 가져오기
  const userProfile = JSON.parse(localStorage.getItem('userProfile') || 'null');
  const anonProfile = JSON.parse(localStorage.getItem('anonProfile') || 'null');
  
  // 학번에서 입학년도 추출 (9자리 학번의 첫 4자리가 입학년도)
  let yearDisplay = null;
  let statusDisplay = null;
  
  if (!isAnonymous && userProfile && userProfile.studentId) {
    const studentId = userProfile.studentId;
    if (studentId.length >= 4) {
      const admissionYear = studentId.substring(0, 4); // 예: "2022"
      yearDisplay = admissionYear.substring(2); // 마지막 2자리: "22"
    }
    statusDisplay = userProfile.status || '재학생';
  } else if (isAnonymous && anonProfile && anonProfile.year) {
    // 익명 프로필에서 학번 정보 가져오기
    yearDisplay = anonProfile.year.replace(/[^0-9]/g, ''); // "22학번" -> "22"
    statusDisplay = null; // 익명일 때는 상태 표시 안함
  }
  
  // 현재 사용자의 학번 (작성자 확인용)
  const currentUserStudentId = userProfile ? userProfile.studentId : null;
  
  const postId = 'p' + Date.now();
  
  // 게시글 작성자는 자동으로 익명1로 설정
  const anonymousId = currentUserStudentId ? getAnonymousIdForPost(postId, currentUserStudentId) : 1;
  
  const newPost = {
    id: postId,
    title: title,
    content: content, // 내용도 저장
    author: '익명' + anonymousId,
    authorStudentId: currentUserStudentId, // 작성자 학번 저장
    year: yearDisplay ? parseInt(yearDisplay) : null,
    status: statusDisplay,
    createdAt: new Date().toISOString(),
    views: 0,
    likes: 0,
    comments: 0,
    tags: tags,
    boardId: currentBoard,
    departmentId: department || null,
    type: type,
    category: categoryName
  };
  
  try {
    // 서버에 게시글 저장
    const response = await fetch('/api/board-posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newPost)
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 서버에서 게시글 다시 로드
      posts = await loadPostsFromServer();
      
      // 마이페이지 활동 기록에 추가
      const currentUser = localStorage.getItem('currentUser');
      if (currentUser) {
        try {
          const activity = JSON.parse(localStorage.getItem(`activity_${currentUser}`) || '{"posts":[],"comments":[],"likes":[],"commentLikes":[]}');
          
          activity.posts.unshift({
            id: newPost.id,
            title: newPost.title,
            content: newPost.content,
            category: newPost.category,
            date: newPost.createdAt,
            likes: 0
          });
          
          localStorage.setItem(`activity_${currentUser}`, JSON.stringify(activity));
        } catch (e) {
          console.error('활동 기록 저장 실패:', e);
        }
      }
      
      hideWriteModal();
      filterAndDisplayPosts();
      
      alert('게시글이 작성되었습니다!');
      console.log('게시글 작성됨:', newPost);
    } else {
      alert(result.message || '게시글 작성 중 오류가 발생했습니다.');
    }
  } catch (error) {
    console.error('게시글 작성 오류:', error);
    alert('게시글 작성 중 오류가 발생했습니다. 다시 시도해주세요.');
  } finally {
    // 제출 완료 - 플래그 해제
    isSubmitting = false;
  }
}

// ===== 게시글 저장/로드 함수 =====
function savePostsToLocalStorage() {
  // 서버 기반으로 변경되어 localStorage 저장 비활성화
  // 게시글은 서버에만 저장됩니다
  console.log('게시글은 서버에 저장됩니다.');
}

async function loadPostsFromServer() {
  try {
    const response = await fetch('/api/board-posts');
    const result = await response.json();
    
    if (result.success && result.posts) {
      console.log('서버에서 게시글 로드됨:', result.posts.length + '개');
      // 서버 게시글과 mockPosts 병합
      return [...result.posts, ...mockPosts];
    }
  } catch (e) {
    console.error('서버에서 게시글 로드 실패:', e);
  }
  return [...mockPosts];
}

function loadPostsFromLocalStorage() {
  try {
    const savedPosts = localStorage.getItem('boardPosts');
    if (savedPosts) {
      const userPosts = JSON.parse(savedPosts);
      console.log('로컬 게시글 로드됨:', userPosts.length + '개');
      // mockPosts와 병합 (사용자 게시글을 앞에 배치)
      return [...userPosts, ...mockPosts];
    }
  } catch (e) {
    console.error('게시글 로드 실패:', e);
  }
  return [...mockPosts];
}

// ===== 이벤트 리스너 =====
document.addEventListener('DOMContentLoaded', async function() {
  // 서버에서 게시글과 댓글 로드
  posts = await loadPostsFromServer();
  comments = await loadCommentsFromServer();
  
  // 익명 번호 매핑 재구성
  rebuildAnonymousMap(posts, comments);
  
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
