const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // 환경 변수에서 proxy 설정 가져오기 (Node.js 환경이므로 process.env 직접 사용)
  // REACT_APP_ 접두사는 React 빌드 시에만 필요하고, Node.js에서는 일반 환경 변수로도 접근 가능
  const proxyPath = process.env.REACT_APP_PROXY_PATH || '/api';
  const proxyTarget = process.env.REACT_APP_PROXY_TARGET || 'http://localhost:8080';

  app.use(
    proxyPath, // proxy가 필요한 path parameter
    createProxyMiddleware({
      target: proxyTarget, // 타겟이 되는 api url
      changeOrigin: true, // 대상 서버 구성에 따라 호스트 헤더가 변경되도록 설정하는 부분입니다.
    })
  );
};