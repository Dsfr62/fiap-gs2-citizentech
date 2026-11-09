package br.com.fiap.gs2.security;

import br.com.fiap.gs2.repository.UsuarioRepository;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/** Le o cabecalho "Authorization: Bearer <token>" e, se o token for valido, autentica o usuario. */
@Component
public class FiltroToken extends OncePerRequestFilter {

    private final TokenService tokenService;
    private final UsuarioRepository usuarios;

    public FiltroToken(TokenService tokenService, UsuarioRepository usuarios) {
        this.tokenService = tokenService;
        this.usuarios = usuarios;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String cabecalho = request.getHeader("Authorization");
        if (cabecalho != null && cabecalho.startsWith("Bearer ")) {
            tokenService.validar(cabecalho.substring(7))
                    .flatMap(usuarios::findByEmail)
                    .ifPresent(usuario -> SecurityContextHolder.getContext().setAuthentication(
                            new UsernamePasswordAuthenticationToken(usuario, null, usuario.getAuthorities())));
        }
        chain.doFilter(request, response);
    }
}
