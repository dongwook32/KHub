document.addEventListener('DOMContentLoaded', function() {
    console.log('KBU Hub 스크립트 로드됨');
    
    // 스크롤 시 헤더 스타일 변경 기능
    const header = document.querySelector('header');
    
    if (header) {
        window.addEventListener('scroll', function() {
            // window.scrollY 값이 50px보다 크면 'scrolled' 클래스 추가, 아니면 제거
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }
});