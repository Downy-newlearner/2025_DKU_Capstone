package com.checkmate.ai.filter;

import com.checkmate.ai.service.JwtTokenProvider;
import com.checkmate.ai.service.TokenService;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.GenericFilterBean;

import java.io.IOException;

@RequiredArgsConstructor
@Slf4j
public class JwtAuthenticationFilter extends GenericFilterBean {
    private final JwtTokenProvider jwtTokenProvider;
    private final TokenService tokenService;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        String requestURI = httpRequest.getRequestURI();
        log.info("Request URI: {}", requestURI);

        // 🔑 인증 예외 경로 설정
        if (isPublicURI(requestURI)) {
            chain.doFilter(request, response);
            return;
        }


        String token = jwtTokenProvider.resolveToken(httpRequest);
        log.info("Extracted Token: {}", token);

        if (token != null) {
            try {
                // 2. 토큰 유효성 및 블랙리스트 검사
                if (jwtTokenProvider.validateToken(token)) {
                    if (tokenService.isTokenBlacklisted(token)) {
                        log.warn("블랙리스트된 토큰: {}", token);
                        handleUnauthorizedResponse(httpResponse, "Token is blacklisted");
                        return;
                    }

                    // 3. 유효한 토큰일 경우 인증 처리
                    Authentication authentication = jwtTokenProvider.getAuthentication(token);
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                } else {
                    throw new JwtException("Invalid token");
                }
            } catch (JwtException e) {
                log.error("JWT 검증 실패: {}", e.getMessage());
                handleUnauthorizedResponse(httpResponse, "Invalid JWT Token");
                return;
            }
        } else {
            log.warn("JWT 토큰이 제공되지 않았습니다.");
            handleUnauthorizedResponse(httpResponse, "JWT token is missing");
            return;
        }


        chain.doFilter(request, response);
    }

    // ✅ 인증 예외 대상 URI (로그인, 회원가입, 비밀번호 재설정 등)
    private boolean isPublicURI(String uri) {
        return uri.startsWith("/sign-in")
                || uri.startsWith("/sign-up")
                || uri.startsWith("/reset-request")
                || uri.startsWith("/reset-password")
                || uri.startsWith("/error");
    }

    // 401 Unauthorized 응답 처리
    private void handleUnauthorizedResponse(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.getWriter().write("{\"error\": \"" + message + "\"}");
        response.getWriter().flush();
    }

}


