package br.com.fiap.gs2.controller;

import br.com.fiap.gs2.dto.Dtos.CanteiroResponse;
import br.com.fiap.gs2.dto.Dtos.LeituraResponse;
import br.com.fiap.gs2.dto.Dtos.RecomendacaoResponse;
import br.com.fiap.gs2.dto.Dtos.RegaResponse;
import br.com.fiap.gs2.repository.CanteiroRepository;
import br.com.fiap.gs2.repository.RecomendacaoRepository;
import br.com.fiap.gs2.repository.RegaRepository;
import br.com.fiap.gs2.service.LeituraService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

/**
 * Exportacao para o pipeline de dados (Area 2). So TECNICO acessa (regra em SegurancaConfig).
 * O pipeline guarda cada resposta como veio, na camada bronze.
 */
@RestController
@RequestMapping("/api/dados")
public class DadosController {

    private final LeituraService leituras;
    private final CanteiroRepository canteiros;
    private final RecomendacaoRepository recomendacoes;
    private final RegaRepository regas;

    public DadosController(LeituraService leituras, CanteiroRepository canteiros,
                           RecomendacaoRepository recomendacoes, RegaRepository regas) {
        this.leituras = leituras;
        this.canteiros = canteiros;
        this.recomendacoes = recomendacoes;
        this.regas = regas;
    }

    /** Sem "desde", devolve os ultimos 7 dias. */
    private static Instant inicio(Instant desde) {
        return desde != null ? desde : Instant.now().minus(Duration.ofDays(7));
    }

    @GetMapping("/leituras")
    public List<LeituraResponse> leituras(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant desde) {
        return leituras.desde(inicio(desde)).stream().map(LeituraResponse::de).toList();
    }

    /** Cadastro dos canteiros (cultura, area, vazao, umidade minima e produtor). Sem a chave do sensor. */
    @GetMapping("/canteiros")
    public List<CanteiroResponse> canteiros() {
        return canteiros.findAll().stream().map(c -> CanteiroResponse.de(c, null)).toList();
    }

    /** Alertas enviados ao produtor (cada recomendacao de regar ou de nao regar). */
    @GetMapping("/recomendacoes")
    public List<RecomendacaoResponse> recomendacoes(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant desde) {
        return recomendacoes.findByCriadaEmAfterOrderByCriadaEmAsc(inicio(desde)).stream()
                .map(RecomendacaoResponse::de).toList();
    }

    /** Regas registradas ("fiz"): o pipeline cruza com os alertas para medir a taxa de "fiz". */
    @GetMapping("/regas")
    public List<RegaResponse> regas(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant desde) {
        return regas.findByFeitaEmAfterOrderByFeitaEmAsc(inicio(desde)).stream().map(RegaResponse::de).toList();
    }
}
