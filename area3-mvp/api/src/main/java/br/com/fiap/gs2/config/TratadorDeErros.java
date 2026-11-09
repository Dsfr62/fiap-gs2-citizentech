package br.com.fiap.gs2.config;

import br.com.fiap.gs2.dto.Dtos.ErroResponse;
import br.com.fiap.gs2.service.Erros;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.LinkedHashMap;
import java.util.Map;

/** Transforma erros em respostas JSON claras, sem vazar detalhe interno (stack trace) para fora. */
@RestControllerAdvice
public class TratadorDeErros {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErroResponse> validacao(MethodArgumentNotValidException e) {
        Map<String, String> campos = new LinkedHashMap<>();
        e.getBindingResult().getFieldErrors().forEach(f -> campos.putIfAbsent(f.getField(), f.getDefaultMessage()));
        return resposta(HttpStatus.BAD_REQUEST, "dados inválidos", campos);
    }

    @ExceptionHandler({HttpMessageNotReadableException.class, MethodArgumentTypeMismatchException.class})
    public ResponseEntity<ErroResponse> formato(Exception e) {
        return resposta(HttpStatus.BAD_REQUEST, "formato inválido", null);
    }

    @ExceptionHandler(Erros.NaoEncontrado.class)
    public ResponseEntity<ErroResponse> naoEncontrado(Erros.NaoEncontrado e) {
        return resposta(HttpStatus.NOT_FOUND, e.getMessage(), null);
    }

    @ExceptionHandler(Erros.ChaveInvalida.class)
    public ResponseEntity<ErroResponse> chave(Erros.ChaveInvalida e) {
        return resposta(HttpStatus.UNAUTHORIZED, e.getMessage(), null);
    }

    @ExceptionHandler(Erros.Conflito.class)
    public ResponseEntity<ErroResponse> conflito(Erros.Conflito e) {
        return resposta(HttpStatus.CONFLICT, e.getMessage(), null);
    }

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErroResponse> login(AuthenticationException e) {
        return resposta(HttpStatus.UNAUTHORIZED, "e-mail ou senha incorretos", null);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErroResponse> acesso(AccessDeniedException e) {
        return resposta(HttpStatus.FORBIDDEN, "acesso negado", null);
    }

    private static ResponseEntity<ErroResponse> resposta(HttpStatus status, String erro, Map<String, String> campos) {
        return ResponseEntity.status(status).body(new ErroResponse(status.value(), erro, campos));
    }
}
