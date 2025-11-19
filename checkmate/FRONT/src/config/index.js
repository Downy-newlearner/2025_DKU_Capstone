/**
 * Application Configuration
 * 
 * 환경 변수를 기반으로 애플리케이션 설정을 중앙 관리합니다.
 * React 환경 변수는 REACT_APP_ 접두사가 필요하며, 빌드 타임에 주입됩니다.
 */

const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  
  // API Base URL 설정
  // 개발 환경: localhost, 프로덕션: 실제 서버 주소
  const apiBaseURL = process.env.REACT_APP_API_BASE_URL || '/api';

  return {
    // API 설정
    api: {
      baseURL: apiBaseURL,
      timeout: parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000,
      withCredentials: true,
    },
    
    // Proxy 설정 (개발 환경용)
    proxy: {
      path: process.env.REACT_APP_PROXY_PATH || '/api2',
      target: process.env.REACT_APP_PROXY_TARGET || 'http://localhost:8080',
    },
    
    // 환경 정보
    env: {
      isDevelopment: env === 'development',
      isProduction: env === 'production',
      nodeEnv: env,
    },
    
    // API 엔드포인트 헬퍼 함수
    endpoints: {
      // 파일 다운로드 URL 생성
      fileDownload: (fileName) => `${apiBaseURL}/file/${encodeURIComponent(fileName)}`,
      
      // 리포트 다운로드 URL 생성
      reportDownload: (subject) => `${apiBaseURL}/report/${encodeURIComponent(subject)}`,
    },
  };
};

// 싱글톤 패턴으로 config 인스턴스 생성
const config = getConfig();

export default config;

