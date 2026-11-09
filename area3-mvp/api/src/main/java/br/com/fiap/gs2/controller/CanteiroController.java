package br.com.fiap.gs2.controller;

import br.com.fiap.gs2.dto.Dtos.*;
import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Usuario;
import br.com.fiap.gs2.service.*;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/canteiros")
public class CanteiroController {

    private final CanteiroService canteiros;
    private final LeituraService leituras;
    private final RecomendacaoService recomendacoes;
    private final RegaService regas;

    public CanteiroController(CanteiroService canteiros, LeituraService leituras,
                              RecomendacaoService recomendacoes, RegaService regas) {
        this.canteiros = canteiros;
        this.leituras = leituras;
        this.recomendacoes = recomendacoes;
        this.regas = regas;
    }

    @GetMapping
    public List<CanteiroResponse> listar(@AuthenticationPrincipal Usuario usuario) {
        return canteiros.listar(usuario).stream()
                .map(c -> CanteiroResponse.de(c, leituras.ultimaOuNulo(c.getId())))
                .toList();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CanteiroCriadoResponse criar(@RequestBody @Valid CanteiroRequest pedido,
                                        @AuthenticationPrincipal Usuario usuario) {
        Canteiro canteiro = canteiros.criar(pedido, usuario);
        return new CanteiroCriadoResponse(CanteiroResponse.de(canteiro, null), canteiro.getChaveDispositivo());
    }

    @GetMapping("/{id}")
    public CanteiroResponse buscar(@PathVariable Long id, @AuthenticationPrincipal Usuario usuario) {
        Canteiro canteiro = canteiros.buscarPermitido(id, usuario);
        return CanteiroResponse.de(canteiro, leituras.ultimaOuNulo(id));
    }

    @GetMapping("/{id}/leituras")
    public List<LeituraResponse> leituras(@PathVariable Long id,
                                          @RequestParam(defaultValue = "24") int limite,
                                          @AuthenticationPrincipal Usuario usuario) {
        canteiros.buscarPermitido(id, usuario);
        return leituras.ultimas(id, limite).stream().map(LeituraResponse::de).toList();
    }

    @GetMapping("/{id}/recomendacoes/ultima")
    public RecomendacaoResponse ultimaRecomendacao(@PathVariable Long id, @AuthenticationPrincipal Usuario usuario) {
        canteiros.buscarPermitido(id, usuario);
        return recomendacoes.ultima(id).map(RecomendacaoResponse::de)
                .orElseThrow(() -> new Erros.NaoEncontrado("ainda nao ha recomendacao para este canteiro"));
    }

    /** "Pedir recomendacao": a API pergunta a IA (ou usa a regra basica) com a ultima leitura. */
    @PostMapping("/{id}/recomendacoes")
    @ResponseStatus(HttpStatus.CREATED)
    public RecomendacaoResponse recomendar(@PathVariable Long id, @AuthenticationPrincipal Usuario usuario) {
        return RecomendacaoResponse.de(recomendacoes.gerar(canteiros.buscarPermitido(id, usuario)));
    }

    @GetMapping("/{id}/regas")
    public List<RegaResponse> regas(@PathVariable Long id, @AuthenticationPrincipal Usuario usuario) {
        canteiros.buscarPermitido(id, usuario);
        return regas.listar(id).stream().map(RegaResponse::de).toList();
    }

    /** "Reguei": registra a rega feita, em minutos; a API converte em litros pela vazao. */
    @PostMapping("/{id}/regas")
    @ResponseStatus(HttpStatus.CREATED)
    public RegaResponse registrarRega(@PathVariable Long id, @RequestBody @Valid RegaRequest pedido,
                                      @AuthenticationPrincipal Usuario usuario) {
        return RegaResponse.de(regas.registrar(canteiros.buscarPermitido(id, usuario), pedido));
    }
}
