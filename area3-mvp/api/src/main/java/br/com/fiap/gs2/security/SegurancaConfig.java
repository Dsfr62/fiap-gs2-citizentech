package br.com.fiap.gs2.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * Regras de acesso da API:
 * - login, cadastro, envio de leitura do sensor (que tem a propria chave), saude e Swagger sao abertos;
 * - /api/dados/** (exportacao para o pipeline) so para TECNICO;
 * - todo o resto exige token.
 */
@Configuration
public class SegurancaConfig {

    @Bean
    public SecurityFilterChain filtros(HttpSecurity http, FiltroToken filtroToken) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable) // API sem sessao nem cookie: CSRF nao se aplica
                .cors(cors -> {})
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(req -> req
                        .requestMatchers(HttpMethod.POST, "/api/auth/login", "/api/auth/cadastro").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/leituras").permitAll()
                        .requestMatchers("/actuator/health/**", "/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**").permitAll()
                        .requestMatchers("/error").permitAll() // sem isso, um erro 500 aparece como 401 e esconde a causa
                        .requestMatchers("/api/dados/**").hasRole("TECNICO")
                        .anyRequest().authenticated())
                .exceptionHandling(e -> e.authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)))
                .addFilterBefore(filtroToken, UsernamePasswordAuthenticationFilter.class)
                .build();
    }

    /** BCrypt: a senha vira um hash com sal; nem quem le o banco descobre a senha. */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    /** Libera o app (Expo web) a chamar a API de outra porta. */
    @Bean
    public CorsConfigurationSource corsConfigurationSource(@Value("${cors.origens}") String origens) {
        CorsConfiguration cors = new CorsConfiguration();
        cors.setAllowedOriginPatterns(Arrays.stream(origens.split(",")).map(String::trim).toList());
        cors.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        cors.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Chave-Dispositivo"));
        UrlBasedCorsConfigurationSource fonte = new UrlBasedCorsConfigurationSource();
        fonte.registerCorsConfiguration("/**", cors);
        return fonte;
    }
}
