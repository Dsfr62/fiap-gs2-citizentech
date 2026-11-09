package br.com.fiap.gs2.controller;

import br.com.fiap.gs2.dto.Dtos.LeituraRequest;
import br.com.fiap.gs2.dto.Dtos.LeituraResponse;
import br.com.fiap.gs2.service.LeituraService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

/** Porta de entrada dos sensores (Arduino ou simulador). Autentica pela chave do canteiro, nao por login. */
@RestController
@RequestMapping("/api/leituras")
public class LeituraController {

    private final LeituraService leituras;

    public LeituraController(LeituraService leituras) {
        this.leituras = leituras;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public LeituraResponse registrar(@RequestHeader(value = "X-Chave-Dispositivo", required = false) String chave,
                                     @RequestBody @Valid LeituraRequest pedido) {
        return LeituraResponse.de(leituras.registrar(chave, pedido));
    }
}
