package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.PedidoIa;
import br.com.fiap.gs2.dto.Dtos.RespostaIa;
import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Leitura;
import br.com.fiap.gs2.model.Recomendacao;
import br.com.fiap.gs2.repository.RecomendacaoRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

@Service
public class RecomendacaoService {

    private final LeituraService leituras;
    private final RecomendacaoRepository recomendacoes;
    private final IaClient ia;

    public RecomendacaoService(LeituraService leituras, RecomendacaoRepository recomendacoes, IaClient ia) {
        this.leituras = leituras;
        this.recomendacoes = recomendacoes;
        this.ia = ia;
    }

    /** Pega a ultima leitura do canteiro, pergunta a IA e, se ela nao responder, usa a regra basica. */
    public Recomendacao gerar(Canteiro canteiro) {
        Leitura leitura = leituras.ultimaOuNulo(canteiro.getId());
        if (leitura == null) {
            throw new Erros.Conflito("o canteiro ainda não tem leitura de sensor");
        }
        PedidoIa pedido = new PedidoIa(canteiro.getId(), canteiro.getCultura().name(), canteiro.getAreaM2(),
                canteiro.getVazaoLitrosMin(), canteiro.getLatitude(), canteiro.getLongitude(),
                leitura.getUmidadeSolo(), leitura.getTemperaturaAr(), leitura.getLuminosidade(),
                canteiro.getCultura().getUmidadeMinimaPercentual());

        Optional<RespostaIa> respostaIa = ia.recomendar(pedido);
        Recomendacao recomendacao = respostaIa
                .map(r -> new Recomendacao(canteiro, Instant.now(), r.regar(), Math.max(0, r.minutos()),
                        Math.round(Math.max(0, r.minutos()) * canteiro.getVazaoLitrosMin()),
                        limitar(r.explicacao()), "IA", leitura.getUmidadeSolo(), r.chuvaPrevistaMm()))
                .orElseGet(() -> {
                    RegraBasica.Decisao d = RegraBasica.decidir(canteiro, leitura);
                    return new Recomendacao(canteiro, Instant.now(), d.regar(), d.minutos(), d.litros(),
                            d.explicacao(), "REGRA_BASICA", leitura.getUmidadeSolo(), null);
                });
        return recomendacoes.save(recomendacao);
    }

    public Optional<Recomendacao> ultima(Long canteiroId) {
        return recomendacoes.findFirstByCanteiroIdOrderByCriadaEmDesc(canteiroId);
    }

    private static String limitar(String texto) {
        if (texto == null || texto.isBlank()) {
            return "Recomendação da IA sem explicação.";
        }
        return texto.length() <= 1000 ? texto : texto.substring(0, 997) + "...";
    }
}
