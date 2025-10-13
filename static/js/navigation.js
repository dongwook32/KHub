/**
 * KBU Hub 공용 네비게이션 컴포넌트
 * CSS Cascade Layers 기반 완전한 스타일 통제 시스템
 */

class NavigationManager {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.navItems = [
            { label: '서비스 소개', href: '/', route: 'index' },
            { label: '랜덤 매칭', href: '/chat', route: 'chat' },
            { label: '게시판', href: '/boards', route: 'boards' },
            { label: '마이페이지', href: '/mypage', route: 'mypage' },
            { label: '로그인', href: '/login', route: 'login' }
        ];
        
        this.isInitialized = false;
        this.init();
    }

    /**
     * 현재 페이지 식별 (Flask 라우트 지원)
     */
    getCurrentPage() {
        // Flask 라우트 경로 가져오기
        const path = window.location.pathname;
        
        console.log('🔄 현재 경로:', path);
        
        // 루트 경로는 'index'로 변환
        if (path === '/' || path === '/index') {
            return 'index';
        }
        
        // 첫 번째 슬래시 제거하고 경로 반환
        const route = path.replace('/', '') || 'index';
        
        // 프로필 설정은 채팅의 하위 페이지
        if (route === 'profile-setup') {
            return 'chat';
        }
        
        console.log('🔄 현재 페이지:', route);
        return route;
    }

    /**
     * 네비게이션 아이템이 활성화되어야 하는지 확인
     */
    isActive(href, route) {
        const currentPage = this.currentPage;
        
        console.log('🔍 활성 상태 확인:', { href, route, currentPage });
        
        // 정확한 매치
        if (route === currentPage) {
            console.log('✅ 정확한 매치:', route, currentPage);
            return true;
        }
        
        console.log('❌ 매치되지 않음:', route, currentPage);
        return false;
    }

    /**
     * 데스크톱 네비게이션 렌더링
     */
    renderDesktopNav() {
        const navPill = document.getElementById('navPill');
        if (!navPill) return;

        // nav-wrap 클래스 추가 (CSS Cascade Layers 시스템 지원)
        navPill.classList.add('nav-wrap');
        navPill.setAttribute('data-component', 'nav');

        navPill.innerHTML = this.navItems.map(item => {
            const isActive = this.isActive(item.href, item.route);
            const activeClass = isActive ? 'is-active' : '';
            
            return `
                <a class="nav-item ${activeClass}" 
                   data-route="${item.route}" 
                   href="${item.href}">
                    ${item.label}
                </a>
            `;
        }).join('');
    }

    /**
     * 모바일 네비게이션 렌더링
     */
    renderMobileNav() {
        const mobileNav = document.getElementById('mobileNav');
        if (!mobileNav) return;

        const navContainer = mobileNav.querySelector('.flex.flex-col.gap-1.py-2.text-sm');
        if (!navContainer) return;

        navContainer.innerHTML = this.navItems.map(item => {
            const isActive = this.isActive(item.href, item.route);
            const activeClass = isActive ? 'active' : '';
            
            return `
                <a class="py-2 ${activeClass}" href="${item.href}">
                    ${item.label}
                </a>
            `;
        }).join('');
    }

    /**
     * 모바일 메뉴 토글 기능
     */
    initMobileMenu() {
        const menuBtn = document.getElementById('menuBtn');
        const mobileNav = document.getElementById('mobileNav');
        
        if (menuBtn && mobileNav) {
            // 메뉴 버튼 클릭 시 토글
            menuBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                mobileNav.classList.toggle('hidden');
                console.log('📱 모바일 메뉴 토글:', !mobileNav.classList.contains('hidden'));
            });
            
            // 모바일 메뉴 아이템 클릭 시 메뉴 닫기
            const mobileNavLinks = mobileNav.querySelectorAll('a');
            mobileNavLinks.forEach(link => {
                link.addEventListener('click', () => {
                    mobileNav.classList.add('hidden');
                    console.log('📱 모바일 메뉴 닫힘 (링크 클릭)');
                });
            });
            
            // 모바일 메뉴 외부 클릭 시 메뉴 닫기
            document.addEventListener('click', (e) => {
                if (!mobileNav.classList.contains('hidden') && 
                    !menuBtn.contains(e.target) && 
                    !mobileNav.contains(e.target)) {
                    mobileNav.classList.add('hidden');
                    console.log('📱 모바일 메뉴 닫힘 (외부 클릭)');
                }
            });
        }
    }

    /**
     * 네비게이션 초기화 (리마운트 방지)
     */
    init() {
        // 이미 초기화되었는지 확인
        if (this.isInitialized) {
            console.log('🔄 네비게이션 이미 초기화됨, 업데이트만 수행');
            this.updateNavigation();
            return;
        }
        
        // DOM이 로드된 후 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.renderDesktopNav();
                this.renderMobileNav();
                this.initMobileMenu();
            });
        } else {
            this.renderDesktopNav();
            this.renderMobileNav();
            this.initMobileMenu();
        }
        
        this.isInitialized = true;
    }
    
    /**
     * 네비게이션 업데이트 (리마운트 없이)
     */
    updateNavigation() {
        // 현재 페이지 상태만 업데이트
        const newCurrentPage = this.getCurrentPage();
        
        // 페이지가 변경되지 않았으면 업데이트 스킵
        if (newCurrentPage === this.currentPage) {
            return;
        }
        
        this.currentPage = newCurrentPage;
        console.log('🔄 네비게이션 업데이트 - 현재 페이지:', this.currentPage);
        
        // 활성 상태만 업데이트 (전체 리렌더링 방지)
        const navItems = document.querySelectorAll('.nav-item');
        console.log('📋 네비게이션 아이템 개수:', navItems.length);
        
        navItems.forEach(item => {
            const route = item.getAttribute('data-route');
            
            console.log('🔍 네비게이션 아이템 확인:', route, '현재 페이지:', this.currentPage);
            
            const isActive = this.isActive(null, route);
            
            if (isActive) {
                item.classList.add('is-active');
                console.log('✅ 활성 상태 적용:', item.textContent);
            } else {
                item.classList.remove('is-active');
            }
        });
        
        // 모바일 네비게이션도 업데이트
        const mobileNavItems = document.querySelectorAll('#mobileNav .py-2');
        mobileNavItems.forEach(item => {
            const href = item.getAttribute('href');
            const route = href.replace('/', '') || 'index';
            const isActive = this.isActive(null, route);
            
            if (isActive) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    /**
     * 현재 페이지 업데이트 (페이지 전환 시 호출)
     */
    updateCurrentPage() {
        // 리마운트 방지를 위해 updateNavigation 사용 (페이지 변경 감지 포함)
        this.updateNavigation();
    }
}

// 전역 네비게이션 매니저 인스턴스 생성
window.NavigationManager = new NavigationManager();

// 페이지 전환 시 네비게이션 업데이트
window.addEventListener('popstate', () => {
    window.NavigationManager.updateCurrentPage();
});

// 페이지 로드 완료 시 네비게이션 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.NavigationManager.init();
    });
} else {
    window.NavigationManager.init();
}
