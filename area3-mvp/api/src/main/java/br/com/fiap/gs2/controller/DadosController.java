package br.com.fiap.gs2.controller;

import br.com.fiap.gs2.dto.Dtos.LeituraResponse;
import br.com.fiap.gs2.service.LeituraService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

/** Exportacao para o pipeline de dados (Area 2). So TECNICO acessa (regra em SegurancaConfig). */
@RestController
@RequestMapping("/api/dados")
public class DadosController {

    private final LeituraService leituras;

    public DadosController(LeituraService leituras) {
        this.leituras = leituras;
    }

    @GetMapping("/leituras")
    public List<LeituraResponse> leituras(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant desde) {
        Instant inicio = desde != null ? desde : Instant.now().minus(Duration.ofDays(7));
        return leituras.desde(inicio).stream().map(LeituraResponse::de).toList();
    }
}
