/**
 * KBU Hub - 회원가입 폼 검증 스크립트
 * 실시간 검증, 접근성, 사용자 경험 최적화
 */

(function() {
  'use strict';

  // ========== 유틸리티 함수 ==========
  
  /**
   * 전역 알림 표시
   */
  function showAlert(message, type = 'error') {
    const alert = document.getElementById('globalAlert');
    const alertMessage = document.getElementById('alertMessage');
    
    alertMessage.textContent = message;
    alert.className = 'global-alert alert-' + type;
    alert.style.display = 'flex';
    
    // 5초 후 자동 숨김
    setTimeout(() => {
      closeAlert();
    }, 5000);
  }
  
  /**
   * 전역 알림 닫기
   */
  window.closeAlert = function() {
    const alert = document.getElementById('globalAlert');
    alert.style.display = 'none';
  };

  /**
   * 에러 메시지 표시
   */
  function showError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const errorElement = document.getElementById(fieldId + 'Error');
    
    if (input && errorElement) {
      input.classList.add('is-invalid');
      input.classList.remove('is-valid');
      input.setAttribute('aria-invalid', 'true');
      errorElement.textContent = message;
    }
  }

  /**
   * 에러 메시지 제거
   */
  function clearError(fieldId) {
    const input = document.getElementById(fieldId);
    const errorElement = document.getElementById(fieldId + 'Error');
    
    if (input && errorElement) {
      input.classList.remove('is-invalid');
      input.setAttribute('aria-invalid', 'false');
      errorElement.textContent = '';
    }
  }

  /**
   * 성공 상태 표시
   */
  function showSuccess(fieldId) {
    const input = document.getElementById(fieldId);
    
    if (input) {
      input.classList.add('is-valid');
      input.classList.remove('is-invalid');
      input.setAttribute('aria-invalid', 'false');
    }
  }

  /**
   * 첫 번째 에러 필드로 스크롤 및 포커스
   */
  function focusFirstError() {
    const firstInvalid = document.querySelector('.is-invalid');
    
    if (firstInvalid) {
      firstInvalid.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
      
      setTimeout(() => {
        firstInvalid.focus();
      }, 300);
    }
  }

  // ========== 검증 함수 ==========

  /**
   * 이름 검증
   */
  function validateName() {
    const name = document.getElementById('name');
    const value = name.value.trim();
    
    if (!value) {
      showError('name', '이름을 입력해주세요.');
      return false;
    }
    
    if (value.length > 11) {
      showError('name', '이름은 최대 11자까지 입력 가능합니다.');
      return false;
    }
    
    clearError('name');
    showSuccess('name');
    return true;
  }

  /**
   * 학번 중복 체크 (서버 API 사용)
   */
  async function checkStudentIdDuplicate(studentId) {
    try {
      const response = await fetch('/api/check-student-id', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ student_id: studentId })
      });
      
      const data = await response.json();
      return data.duplicate;
    } catch (e) {
      console.error('학번 중복 체크 실패:', e);
      return false;
    }
  }

  /**
   * 학번 검증 (숫자만, 정확히 9자, 중복 체크)
   */
  async function validateStudentId() {
    const studentId = document.getElementById('student_id');
    const value = studentId.value.trim();
    const pattern = /^\d{9}$/;
    
    if (!value) {
      showError('student_id', '학번을 입력해주세요.');
      return false;
    }
    
    if (!pattern.test(value)) {
      showError('student_id', '학번은 숫자 9자리로 입력해주세요.');
      return false;
    }
    
    // 학번 중복 체크 (서버 API 호출)
    const isDuplicate = await checkStudentIdDuplicate(value);
    if (isDuplicate) {
      showError('student_id', '이미 존재하는 학번입니다. 다른 학번으로 회원가입해주세요.');
      return false;
    }
    
    clearError('student_id');
    showSuccess('student_id');
    return true;
  }

  /**
   * 생일 검증 (미래 날짜 불가)
   */
  function validateBirthday() {
    const birthday = document.getElementById('birthday');
    const value = birthday.value;
    
    if (!value) {
      showError('birthday', '생일을 선택해주세요.');
      return false;
    }
    
    const selectedDate = new Date(value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate > today) {
      showError('birthday', '미래 날짜는 선택할 수 없습니다.');
      return false;
    }
    
    clearError('birthday');
    showSuccess('birthday');
    return true;
  }

  /**
   * 성별 검증
   */
  function validateGender() {
    const genderInputs = document.querySelectorAll('input[name="gender"]');
    const checked = Array.from(genderInputs).some(input => input.checked);
    
    if (!checked) {
      showError('gender', '성별을 선택해주세요.');
      return false;
    }
    
    clearError('gender');
    return true;
  }

  /**
   * 재학 상태 검증
   */
  function validateStatus() {
    const status = document.getElementById('status');
    const value = status.value;
    
    if (!value) {
      showError('status', '재학 상태를 선택해주세요.');
      return false;
    }
    
    clearError('status');
    showSuccess('status');
    return true;
  }

  /**
   * 이메일 검증 (@bible.ac.kr 도메인 강제)
   */
  function validateEmail() {
    const email = document.getElementById('email');
    const value = email.value.trim();
    const pattern = /@bible\.ac\.kr$/i;
    
    if (!value) {
      showError('email', '이메일을 입력해주세요.');
      return false;
    }
    
    if (!pattern.test(value)) {
      showError('email', '@bible.ac.kr 도메인만 사용 가능합니다.');
      return false;
    }
    
    clearError('email');
    showSuccess('email');
    return true;
  }

  /**
   * 비밀번호 강도 검증 (8~15자)
   */
  function validatePassword() {
    const password = document.getElementById('password');
    const value = password.value;
    
    if (!value) {
      showError('password', '비밀번호를 입력해주세요.');
      return false;
    }
    
    if (value.length < 8) {
      showError('password', '비밀번호는 최소 8자 이상이어야 합니다.');
      return false;
    }
    
    if (value.length > 15) {
      showError('password', '비밀번호는 최대 15자까지 입력 가능합니다.');
      return false;
    }
    
    // 영문/숫자/특수문자 중 2종 이상 조합 체크
    const hasLetter = /[a-zA-Z]/.test(value);
    const hasNumber = /\d/.test(value);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value);
    const typesCount = [hasLetter, hasNumber, hasSpecial].filter(Boolean).length;
    
    if (typesCount < 2) {
      showError('password', '영문, 숫자, 특수문자 중 2종 이상을 조합해주세요.');
      return false;
    }
    
    clearError('password');
    showSuccess('password');
    
    // 비밀번호 재확인도 함께 검증
    if (document.getElementById('password_confirm').value) {
      validatePasswordConfirm();
    }
    
    return true;
  }

  /**
   * 비밀번호 재확인 검증
   */
  function validatePasswordConfirm() {
    const password = document.getElementById('password');
    const passwordConfirm = document.getElementById('password_confirm');
    const successElement = document.getElementById('passwordConfirmSuccess');
    
    const value = passwordConfirm.value;
    
    if (!value) {
      showError('password_confirm', '비밀번호를 다시 입력해주세요.');
      successElement.style.display = 'none';
      return false;
    }
    
    if (value !== password.value) {
      showError('password_confirm', '비밀번호가 일치하지 않습니다.');
      successElement.style.display = 'none';
      return false;
    }
    
    clearError('password_confirm');
    showSuccess('password_confirm');
    successElement.style.display = 'block';
    return true;
  }

  // ========== 폼 초기화 ==========

  document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');
    
    if (!form) {
      console.error('회원가입 폼을 찾을 수 없습니다.');
      return;
    }

    // ========== 실시간 검증 ==========
    
    // 이름
    const nameInput = document.getElementById('name');
    nameInput.addEventListener('blur', validateName);
    nameInput.addEventListener('input', function() {
      if (this.value.trim()) {
        validateName();
      }
    });

    // 학번
    const studentIdInput = document.getElementById('student_id');
    studentIdInput.addEventListener('blur', async function() {
      await validateStudentId();
    });
    studentIdInput.addEventListener('input', async function() {
      // 숫자만 입력 허용
      this.value = this.value.replace(/[^\d]/g, '');
      
      // 9자리 제한
      if (this.value.length > 9) {
        this.value = this.value.slice(0, 9);
      }
      
      if (this.value.length === 9) {
        await validateStudentId();
      }
    });

    // 생일
    const birthdayInput = document.getElementById('birthday');
    birthdayInput.addEventListener('change', validateBirthday);
    
    // 오늘 날짜를 max로 설정
    const today = new Date().toISOString().split('T')[0];
    birthdayInput.setAttribute('max', today);

    // 성별
    const genderInputs = document.querySelectorAll('input[name="gender"]');
    genderInputs.forEach(input => {
      input.addEventListener('change', validateGender);
    });

    // 재학 상태
    const statusSelect = document.getElementById('status');
    statusSelect.addEventListener('change', validateStatus);

    // 이메일
    const emailInput = document.getElementById('email');
    emailInput.addEventListener('blur', validateEmail);
    emailInput.addEventListener('input', function() {
      if (this.value.includes('@')) {
        validateEmail();
      }
    });

    // 비밀번호
    const passwordInput = document.getElementById('password');
    passwordInput.addEventListener('blur', validatePassword);
    passwordInput.addEventListener('input', function() {
      if (this.value.length >= 8) {
        validatePassword();
      }
    });

    // 비밀번호 재확인
    const passwordConfirmInput = document.getElementById('password_confirm');
    passwordConfirmInput.addEventListener('blur', validatePasswordConfirm);
    passwordConfirmInput.addEventListener('input', validatePasswordConfirm);

    // ========== 폼 제출 ==========
    
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      // 모든 검증 실행 (비동기 함수 포함)
      const validations = await Promise.all([
        validateName(),
        validateStudentId(),
        validateBirthday(),
        validateGender(),
        validateStatus(),
        validateEmail(),
        validatePassword(),
        validatePasswordConfirm()
      ]);
      
      const isValid = validations.every(result => result === true);
      
      if (!isValid) {
        showAlert('입력하신 정보를 확인해주세요.', 'error');
        focusFirstError();
        return false;
      }
      
      // 폼 제출
      form.classList.add('form-loading');
      
      // 실제 제출
      this.submit();
    });

    // ========== 초기화 ==========
    
    console.log('회원가입 폼 초기화 완료');
  });

})();

