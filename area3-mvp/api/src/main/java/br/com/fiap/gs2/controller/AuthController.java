package br.com.fiap.gs2.controller;

import br.com.fiap.gs2.dto.Dtos.*;
import br.com.fiap.gs2.model.Usuario;
import br.com.fiap.gs2.security.TokenService;
import br.com.fiap.gs2.service.AutenticacaoService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Locale;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final TokenService tokenService;
    private final AutenticacaoService autenticacao;

    public AuthController(AuthenticationManager authenticationManager, TokenService tokenService,
                          AutenticacaoService autenticacao) {
        this.authenticationManager = authenticationManager;
        this.tokenService = tokenService;
        this.autenticacao = autenticacao;
    }

    /** Confere e-mail e senha (BCrypt) e devolve o token que o app usa nas outras chamadas. */
    @PostMapping("/login")
    public TokenResponse login(@RequestBody @Valid LoginRequest pedido) {
        var autenticado = authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(
                pedido.email().trim().toLowerCase(Locale.ROOT), pedido.senha()));
        Usuario usuario = (Usuario) autenticado.getPrincipal();
        return new TokenResponse(tokenService.gerar(usuario), usuario.getNome(), usuario.getPapel());
    }

    @PostMapping("/cadastro")
    @ResponseStatus(HttpStatus.CREATED)
    public UsuarioResponse cadastrar(@RequestBody @Valid CadastroRequest pedido) {
        return UsuarioResponse.de(autenticacao.cadastrar(pedido));
    }

    @GetMapping("/eu")
    public UsuarioResponse eu(@AuthenticationPrincipal Usuario usuario) {
        return UsuarioResponse.de(usuario);
    }
}
