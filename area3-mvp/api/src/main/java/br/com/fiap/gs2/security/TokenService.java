package br.com.fiap.gs2.security;

import br.com.fiap.gs2.model.Usuario;
import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Optional;

/**
 * Gera e confere o token JWT do login. O segredo vem da variavel de ambiente JWT_SEGREDO;
 * o valor padrao so serve para rodar localmente e nunca vai para producao.
 */
@Service
public class TokenService {

    private static final String EMISSOR = "gs2-citizentech";

    private final Algorithm algoritmo;
    private final Duration validade;

    public TokenService(@Value("${seguranca.jwt.segredo}") String segredo,
                        @Value("${seguranca.jwt.validade-horas:8}") long validadeHoras) {
        this.algoritmo = Algorithm.HMAC256(segredo);
        this.validade = Duration.ofHours(validadeHoras);
    }

    public String gerar(Usuario usuario) {
        return JWT.create()
                .withIssuer(EMISSOR)
                .withSubject(usuario.getEmail())
                .withClaim("papel", usuario.getPapel().name())
                .withExpiresAt(Instant.now().plus(validade))
                .sign(algoritmo);
    }

    /** Devolve o e-mail do dono do token, ou vazio se o token for invalido ou vencido. */
    public Optional<String> validar(String token) {
        try {
            return Optional.of(JWT.require(algoritmo).withIssuer(EMISSOR).build().verify(token).getSubject());
        } catch (JWTVerificationException e) {
            return Optional.empty();
        }
    }
}
