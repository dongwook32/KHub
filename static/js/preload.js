/**
 * KBU Hub 프리로드/프리패치 시스템
 * 페이지 전환 성능 최적화를 위한 리소스 사전 로딩
 */

class PreloadManager {
    constructor() {
        this.preloadedRoutes = new Set();
        this.preloadQueue = [];
        this.isPreloading = false;
        
        this.init();
    }
    
    init() {
        // 초기 페이지 로드 후 프리로드 시작
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.startPreloading();
            });
        } else {
            this.startPreloading();
        }
        
        // 사용자 상호작용 감지 후 프리로드
        this.setupInteractionListeners();
        
        console.log('🚀 프리로드 매니저 초기화 완료');
    }
    
    startPreloading() {
        // 주요 라우트 프리로드 (우선순위 순)
        const priorityRoutes = [
            { route: '/', priority: 1 },
            { route: '/chat', priority: 2 },
            { route: '/boards', priority: 3 },
            { route: '/mypage', priority: 4 },
            { route: '/login', priority: 5 }
        ];
        
        // 우선순위에 따라 프리로드
        this.preloadRoutesWithPriority(priorityRoutes);
    }
    
    /**
     * 우선순위에 따른 라우트 프리로드
     */
    async preloadRoutesWithPriority(priorityRoutes) {
        // 우선순위 순으로 정렬
        priorityRoutes.sort((a, b) => a.priority - b.priority);
        
        for (const { route } of priorityRoutes) {
            try {
                await this.preloadRoute(route);
                // 각 프리로드 사이에 짧은 지연
                await this.delay(100);
            } catch (error) {
                console.warn(`⚠️ 프리로드 실패: ${route}`, error);
            }
        }
    }
    
    /**
     * 지연 함수
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    setupInteractionListeners() {
        // 마우스 오버 시 프리로드 (지연 적용)
        document.addEventListener('mouseover', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.isInternalRoute(link.href)) {
                const route = this.extractRoute(link.href);
                if (!this.preloadedRoutes.has(route)) {
                    // 300ms 지연 후 프리로드 (실제 클릭 시에는 이미 로드됨)
                    setTimeout(() => {
                        this.preloadRoute(route);
                    }, 300);
                }
            }
        });
        
        // 네비게이션 아이템 호버 시 프리로드
        document.addEventListener('mouseover', (e) => {
            const navItem = e.target.closest('.nav-item');
            if (navItem) {
                const href = navItem.getAttribute('href');
                if (href) {
                    const route = this.extractRoute(href);
                    if (!this.preloadedRoutes.has(route)) {
                        // 네비게이션은 즉시 프리로드
                        this.preloadRoute(route);
                    }
                }
            }
        });
        
        // 터치 시작 시 프리로드 (모바일)
        document.addEventListener('touchstart', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.isInternalRoute(link.href)) {
                const route = this.extractRoute(link.href);
                if (!this.preloadedRoutes.has(route)) {
                    this.preloadRoute(route);
                }
            }
        });
        
        // 포커스 시 프리로드 (키보드 네비게이션)
        document.addEventListener('focusin', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.isInternalRoute(link.href)) {
                const route = this.extractRoute(link.href);
                if (!this.preloadedRoutes.has(route)) {
                    this.preloadRoute(route);
                }
            }
        });
    }
    
    isInternalRoute(href) {
        try {
            const url = new URL(href, window.location.origin);
            return url.origin === window.location.origin && 
                   (url.pathname.endsWith('.html') || url.pathname === '/' || url.pathname === '/index');
        } catch {
            return false;
        }
    }
    
    extractRoute(href) {
        try {
            const url = new URL(href, window.location.origin);
            let pathname = url.pathname;
            
            // HTML 확장자 제거
            if (pathname.endsWith('.html')) {
                pathname = pathname.replace('.html', '');
            }
            
            // 기본 라우트 정규화
            if (pathname === '/index' || pathname === '/index.html') {
                pathname = '/';
            }
            
            return pathname;
        } catch {
            return href;
        }
    }
    
    async preloadRoutes(routes) {
        for (const route of routes) {
            if (!this.preloadedRoutes.has(route)) {
                this.preloadQueue.push(route);
            }
        }
        
        if (!this.isPreloading) {
            this.processPreloadQueue();
        }
    }
    
    async preloadRoute(route) {
        if (this.preloadedRoutes.has(route)) {
            return;
        }
        
        try {
            const routeMap = {
                '/': 'index.html',
                '/chat': 'chat.html',
                '/boards': 'boards.html',
                '/mypage': 'mypage.html',
                '/login': 'login.html',
                '/profile-setup': 'profile-setup.html'
            };
            
            const file = routeMap[route];
            if (!file) {
                console.warn(`⚠️ 알 수 없는 라우트: ${route}`);
                return;
            }
            
            console.log(`🔄 프리로드 시작: ${route} (${file})`);
            
            // Fetch API로 프리로드
            const response = await fetch(file, {
                method: 'GET',
                headers: {
                    'X-Preload': 'true'
                }
            });
            
            if (response.ok) {
                // 응답을 캐시에 저장
                const html = await response.text();
                this.cacheRoute(route, html);
                this.preloadedRoutes.add(route);
                
                console.log(`✅ 프리로드 완료: ${route}`);
            } else {
                console.warn(`⚠️ 프리로드 실패: ${route} (${response.status})`);
            }
            
        } catch (error) {
            console.error(`❌ 프리로드 오류: ${route}`, error);
        }
    }
    
    cacheRoute(route, html) {
        // 메모리 캐시에 저장
        if (!window.routeCache) {
            window.routeCache = new Map();
        }
        
        window.routeCache.set(route, html);
        
        // 로컬 스토리지에도 저장 (선택사항)
        try {
            localStorage.setItem(`route_cache_${route}`, html);
        } catch (e) {
            // 로컬 스토리지 용량 초과 시 무시
        }
    }
    
    getCachedRoute(route) {
        // 메모리 캐시에서 먼저 확인
        if (window.routeCache && window.routeCache.has(route)) {
            return window.routeCache.get(route);
        }
        
        // 로컬 스토리지에서 확인
        try {
            const cached = localStorage.getItem(`route_cache_${route}`);
            if (cached) {
                // 메모리 캐시에도 저장
                if (!window.routeCache) {
                    window.routeCache = new Map();
                }
                window.routeCache.set(route, cached);
                return cached;
            }
        } catch (e) {
            // 로컬 스토리지 접근 실패 시 무시
        }
        
        return null;
    }
    
    async processPreloadQueue() {
        if (this.isPreloading || this.preloadQueue.length === 0) {
            return;
        }
        
        this.isPreloading = true;
        
        while (this.preloadQueue.length > 0) {
            const route = this.preloadQueue.shift();
            await this.preloadRoute(route);
            
            // 다음 프리로드 전 잠시 대기 (브라우저 부하 방지)
            await this.wait(100);
        }
        
        this.isPreloading = false;
    }
    
    // 이미지 프리로드
    preloadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    }
    
    // 폰트 프리로드
    preloadFont(fontFamily, fontWeight = '400') {
        if ('fonts' in document) {
            return document.fonts.load(`${fontWeight} 16px ${fontFamily}`);
        }
        return Promise.resolve();
    }
    
    // CSS 프리로드
    preloadCSS(href) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'style';
            link.href = href;
            link.onload = () => {
                link.rel = 'stylesheet';
                resolve(link);
            };
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }
    
    // JS 프리로드
    preloadJS(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // 공개 메서드들
    isRoutePreloaded(route) {
        return this.preloadedRoutes.has(route);
    }
    
    getPreloadedRoutes() {
        return Array.from(this.preloadedRoutes);
    }
    
    clearCache() {
        if (window.routeCache) {
            window.routeCache.clear();
        }
        
        // 로컬 스토리지 캐시도 삭제
        try {
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('route_cache_')) {
                    localStorage.removeItem(key);
                }
            });
        } catch (e) {
            // 로컬 스토리지 접근 실패 시 무시
        }
        
        this.preloadedRoutes.clear();
        console.log('🗑️ 프리로드 캐시 삭제 완료');
    }
}

// 전역 프리로드 매니저 인스턴스 생성
window.preloadManager = new PreloadManager();

// 외부에서 사용할 수 있는 편의 함수들
window.preloadRoute = (route) => window.preloadManager.preloadRoute(route);
window.isRoutePreloaded = (route) => window.preloadManager.isRoutePreloaded(route);
window.getCachedRoute = (route) => window.preloadManager.getCachedRoute(route);
window.clearPreloadCache = () => window.preloadManager.clearCache();
