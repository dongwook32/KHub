/**
 * KBU Hub SPA 라우터 시스템
 * 페이지 전환 시 깜박임(FOUC/FOUT/CLS) 제거를 위한 클라이언트 사이드 라우팅
 */

class SPARouter {
    constructor() {
        this.routes = {
            '/': 'index.html',
            '/index': 'index.html',
            '/chat': 'chat.html',
            '/boards': 'boards.html',
            '/mypage': 'mypage.html',
            '/login': 'login.html',
            '/profile-setup': 'profile-setup.html'
        };
        
        this.currentRoute = '/';
        this.currentFile = 'index.html';
        this.contentContainer = null;
        this.isNavigating = false;
        
        this.init();
    }
    
    init() {
        // 콘텐츠 컨테이너 설정
        this.contentContainer = document.getElementById('main-content');
        if (!this.contentContainer) {
            console.error('❌ main-content 컨테이너를 찾을 수 없습니다.');
            return;
        }
        
        // 초기 라우트 설정
        this.currentRoute = window.location.pathname || '/';
        
        // 네비게이션 이벤트 리스너 설정
        this.setupNavigationListeners();
        
        // 브라우저 히스토리 이벤트 리스너 설정
        window.addEventListener('popstate', (e) => {
            this.handleRouteChange(e.state?.route || window.location.pathname, false);
        });
        
        // 초기 페이지 로드
        this.handleRouteChange(this.currentRoute, false);
        
        console.log('🚀 SPA 라우터 초기화 완료');
    }
    
    setupNavigationListeners() {
        // 모든 네비게이션 링크에 이벤트 리스너 추가
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (!link) return;
            
            const href = link.getAttribute('href');
            
            // 외부 링크나 앵커 링크는 기본 동작 유지
            if (href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('#')) {
                return;
            }
            
            // HTML 파일 링크는 SPA 라우팅으로 처리
            if (href.endsWith('.html') || href === '/' || href === '/index') {
                e.preventDefault();
                this.navigateTo(href);
            }
        });
        
        // window.location.href 호출을 가로채기
        this.interceptWindowLocation();
    }
    
    interceptWindowLocation() {
        const originalLocation = window.location;
        
        // window.location.href setter를 가로채기
        Object.defineProperty(window.location, 'href', {
            get: function() {
                return originalLocation.href;
            },
            set: function(url) {
                console.log('🔄 window.location.href 가로채기:', url);
                
                // HTML 파일로의 이동인지 확인
                if (url.includes('.html') || url === window.location.origin + '/' || url === window.location.origin + '/index') {
                    const path = new URL(url, window.location.origin).pathname;
                    window.spaRouter.navigateTo(path);
                } else {
                    // 외부 링크는 기본 동작
                    originalLocation.href = url;
                }
            }
        });
    }
    
    navigateTo(route, addToHistory = true) {
        if (this.isNavigating) {
            console.log('⏳ 이미 네비게이션 중입니다.');
            return;
        }
        
        // 라우트 정규화
        const normalizedRoute = this.normalizeRoute(route);
        
        if (normalizedRoute === this.currentRoute) {
            console.log('📍 이미 해당 페이지에 있습니다.');
            return;
        }
        
        console.log(`🔄 페이지 전환: ${this.currentRoute} → ${normalizedRoute}`);
        
        this.isNavigating = true;
        
        // 페이지 전환 상태 추가
        document.body.classList.add('page-transitioning');
        
        // 히스토리 업데이트
        if (addToHistory) {
            history.pushState({ route: normalizedRoute }, '', normalizedRoute);
        }
        
        // 라우트 변경 처리
        this.handleRouteChange(normalizedRoute, true);
    }
    
    normalizeRoute(route) {
        // HTML 확장자 제거
        if (route.endsWith('.html')) {
            route = route.replace('.html', '');
        }
        
        // 슬래시 정규화
        if (!route.startsWith('/')) {
            route = '/' + route;
        }
        
        // 기본 라우트 매핑
        if (route === '/index' || route === '/index.html') {
            route = '/';
        }
        
        return route;
    }
    
    async handleRouteChange(route, animate = true) {
        try {
            const targetFile = this.routes[route];
            if (!targetFile) {
                console.error(`❌ 알 수 없는 라우트: ${route}`);
                return;
            }
            
            // 현재 라우트 업데이트
            this.currentRoute = route;
            this.currentFile = targetFile;
            
            // 네비게이션 활성 상태 업데이트
            this.updateNavigationState(route);
            
            if (animate) {
                // 페이드 아웃 애니메이션
                this.contentContainer.classList.add('content-exit-active');
                this.contentContainer.style.opacity = '0';
                this.contentContainer.style.transform = 'translateY(10px)';
                
                // 애니메이션 완료 대기
                await this.wait(150);
            }
            
            // 콘텐츠 로드
            await this.loadContent(targetFile);
            
            if (animate) {
                // 페이드 인 애니메이션
                this.contentContainer.classList.add('content-enter');
                this.contentContainer.style.opacity = '0';
                this.contentContainer.style.transform = 'translateY(10px)';
                
                // 다음 프레임에서 페이드 인 시작
                requestAnimationFrame(() => {
                    this.contentContainer.classList.remove('content-enter');
                    this.contentContainer.classList.add('content-enter-active');
                    this.contentContainer.style.opacity = '1';
                    this.contentContainer.style.transform = 'translateY(0)';
                });
                
                // 애니메이션 완료 후 스타일 정리
                setTimeout(() => {
                    this.contentContainer.classList.remove('content-enter-active');
                    this.contentContainer.style.transition = '';
                }, 150);
            }
            
            // 페이지별 초기화 함수 호출
            this.initializePage(targetFile);
            
        } catch (error) {
            console.error('❌ 페이지 로드 실패:', error);
        } finally {
            this.isNavigating = false;
        }
    }
    
    async loadContent(file) {
        try {
            // 프리로드된 콘텐츠가 있는지 확인
            const cachedContent = window.getCachedRoute && window.getCachedRoute(this.currentRoute);
            let html;
            
            if (cachedContent) {
                console.log(`✅ 캐시된 콘텐츠 사용: ${file}`);
                html = cachedContent;
            } else {
                console.log(`🔄 네트워크에서 로드: ${file}`);
                const response = await fetch(file);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                html = await response.text();
            }
            
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // 메인 콘텐츠 추출
            const mainContent = doc.querySelector('main') || doc.querySelector('.main-content') || doc.body;
            
            if (mainContent) {
                // 스크립트 태그 제거 (보안상의 이유)
                const scripts = mainContent.querySelectorAll('script');
                scripts.forEach(script => script.remove());
                
                // 콘텐츠 업데이트
                this.contentContainer.innerHTML = mainContent.innerHTML;
                
                // 스타일 태그 추가
                const styles = doc.querySelectorAll('style');
                styles.forEach(style => {
                    if (!document.head.querySelector(`style[data-page="${file}"]`)) {
                        const newStyle = style.cloneNode(true);
                        newStyle.setAttribute('data-page', file);
                        document.head.appendChild(newStyle);
                    }
                });
                
                // 페이지별 스크립트 실행 (Tailwind 설정 제외)
                const scripts = doc.querySelectorAll('script');
                scripts.forEach(script => {
                    // Tailwind 설정은 제외하고 다른 스크립트 실행
                    if (!script.textContent.includes('tailwind.config') && 
                        !script.textContent.includes('tailwind') &&
                        script.textContent.trim().length > 0) {
                        try {
                            // 페이지별 초기화 함수만 실행
                            if (script.textContent.includes('DOMContentLoaded') || 
                                script.textContent.includes('addEventListener')) {
                                eval(script.textContent);
                                console.log(`✅ 페이지 스크립트 로드: ${file}`);
                            }
                        } catch (e) {
                            console.warn(`⚠️ 페이지 스크립트 로드 실패: ${file}`, e);
                        }
                    }
                });
                
                console.log(`✅ 콘텐츠 로드 완료: ${file}`);
            } else {
                throw new Error('메인 콘텐츠를 찾을 수 없습니다.');
            }
            
        } catch (error) {
            console.error(`❌ 콘텐츠 로드 실패: ${file}`, error);
            this.contentContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <h2>페이지를 로드할 수 없습니다</h2>
                    <p>${error.message}</p>
                    <button onclick="window.spaRouter.navigateTo('/')" style="margin-top: 20px; padding: 10px 20px; background: #FF9F7C; color: white; border: none; border-radius: 8px; cursor: pointer;">
                        홈으로 돌아가기
                    </button>
                </div>
            `;
        } finally {
            // 페이지 전환 상태 제거
            setTimeout(() => {
                document.body.classList.remove('page-transitioning');
            }, 150);
        }
    }
    
    updateNavigationState(route) {
        console.log('🔄 네비게이션 상태 업데이트:', route);
        
        // 네비게이션 매니저를 통한 상태 업데이트 (리마운트 방지)
        if (window.NavigationManager && window.NavigationManager.updateCurrentPage) {
            window.NavigationManager.updateCurrentPage();
        } else {
            // 폴백: 직접 DOM 업데이트
            const navItems = document.querySelectorAll('.nav-item');
            console.log('📋 네비게이션 아이템 개수:', navItems.length);
            
            navItems.forEach(item => {
                const href = item.getAttribute('href');
                const itemRoute = this.normalizeRoute(href);
                
                console.log('🔍 네비게이션 아이템 확인:', href, itemRoute, '현재 라우트:', route);
                
                if (itemRoute === route) {
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
                const itemRoute = this.normalizeRoute(href);
                
                if (itemRoute === route) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }
    }
    
    initializePage(file) {
        // 페이지별 초기화 함수 호출
        const pageName = file.replace('.html', '');
        const initFunction = window[`initialize${pageName.charAt(0).toUpperCase() + pageName.slice(1)}`];
        
        if (typeof initFunction === 'function') {
            console.log(`🔧 ${pageName} 페이지 초기화 함수 호출`);
            initFunction();
        }
        
        // 스크롤을 맨 위로
        window.scrollTo(0, 0);
        
        // 페이지 로드 이벤트 발생
        window.dispatchEvent(new CustomEvent('pageLoaded', { 
            detail: { route: this.currentRoute, file: file } 
        }));
    }
    
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // 공개 메서드들
    getCurrentRoute() {
        return this.currentRoute;
    }
    
    getCurrentFile() {
        return this.currentFile || this.routes[this.currentRoute];
    }
    
    // 외부에서 사용할 수 있는 네비게이션 메서드
    goToHome() {
        this.navigateTo('/');
    }
    
    goToChat() {
        this.navigateTo('/chat');
    }
    
    goToBoards() {
        this.navigateTo('/boards');
    }
    
    goToMypage() {
        this.navigateTo('/mypage');
    }
    
    goToLogin() {
        this.navigateTo('/login');
    }
    
    goToProfileSetup() {
        this.navigateTo('/profile-setup');
    }
}

// 전역 라우터 인스턴스 생성
window.spaRouter = new SPARouter();

// 외부에서 사용할 수 있는 편의 함수들
window.navigateTo = (route) => window.spaRouter.navigateTo(route);
window.goToHome = () => window.spaRouter.goToHome();
window.goToChat = () => window.spaRouter.goToChat();
window.goToBoards = () => window.spaRouter.goToBoards();
window.goToMypage = () => window.spaRouter.goToMypage();
window.goToLogin = () => window.spaRouter.goToLogin();
window.goToProfileSetup = () => window.spaRouter.goToProfileSetup();

// 전역 라우터 인스턴스 노출 (NavigationManager에서 접근 가능)
window.spaRouter = window.spaRouter;
