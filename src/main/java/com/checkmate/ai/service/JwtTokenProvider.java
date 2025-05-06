package com.checkmate.ai.service;

import com.checkmate.ai.dto.CustomUserDetails;
import com.checkmate.ai.dto.JwtToken;
import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.security.Key;
import java.util.Date;
import java.util.List;
@Slf4j
@Component
public class JwtTokenProvider {
    private final Key key;


    public JwtTokenProvider(@Value("${jwt.secret}") String secretKey) {
        log.info("JWT Secret Key: {}", secretKey); // 로그 추가

        byte[] keyBytes = Decoders.BASE64.decode(secretKey);
        this.key = Keys.hmacShaKeyFor(keyBytes);
    }


    public JwtToken generateToken(Authentication authentication) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        long now = (new Date()).getTime();
        Date accessTokenExpiresIn = new Date(now + 86400000);
        String accessToken = Jwts.builder()
                .setSubject(userDetails.getEmail())
                .claim("name", userDetails.getName())
                .claim("objectId", userDetails.getObjectId())
                .setExpiration(accessTokenExpiresIn)
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();



        String refreshToken = Jwts.builder()
                .setExpiration(new Date(now + 86400000))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();

        return JwtToken.builder()
                .grantType("Bearer")
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }


    public Authentication getAuthentication(String accessToken) {
        Claims claims = parseClaims(accessToken);
        List<GrantedAuthority> authorities = List.of(new SimpleGrantedAuthority("ROLE_USER"));

        CustomUserDetails principal = CustomUserDetails.builder()
                .name(claims.get("name", String.class))
                .email(claims.getSubject())
                .password("")
                .objectId(claims.get("objectId", String.class))
                .build();
        return new UsernamePasswordAuthenticationToken(principal, "", authorities);
    }


    // 비밀번호 재설정용 토큰 생성
    public String generateResetPasswordToken(String email) {
        long now = (new Date()).getTime();
        Date resetTokenExpiration = new Date(now + 3600000); // 1시간 후 만료
        return Jwts.builder()
                .setSubject(email)
                .setExpiration(resetTokenExpiration)
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    // 토큰 유효성 검사 및 파싱
    public Claims verifyResetToken(String token) {
        try {
            return parseClaims(token);  // 기존의 parseClaims 메서드를 사용하여 토큰을 파싱
        } catch (Exception e) {
            log.error("Token validation failed", e);
            return null;  // 파싱 실패 시 null을 반환
        }
    }


    private Claims parseClaims(String accessToken) {

        try {
            return Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(accessToken)
                    .getBody();
        } catch (ExpiredJwtException e) {
            return e.getClaims();
        }
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            log.info("Invalid JWT Token", e);
        }
        return false;
    }

    public String getUserEmail(String token) {
        return Jwts.parser().setSigningKey(key).parseClaimsJws(token)
                .getBody().getSubject();
    }

    public long getExpiration(String token) {
        Claims claims = Jwts.parser().setSigningKey(key).parseClaimsJws(token).getBody();
        return claims.getExpiration().getTime() - System.currentTimeMillis();
    }


    // Request Header에서 토큰 정보 추출
    public String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7).trim(); // 공백 제거
        }
        return null;
    }



}



