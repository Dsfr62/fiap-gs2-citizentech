package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.LeituraRequest;
import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Leitura;
import br.com.fiap.gs2.repository.CanteiroRepository;
import br.com.fiap.gs2.repository.LeituraRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class LeituraService {

    private final CanteiroRepository canteiros;
    private final LeituraRepository leituras;

    public LeituraService(CanteiroRepository canteiros, LeituraRepository leituras) {
        this.canteiros = canteiros;
        this.leituras = leituras;
    }

    /** O sensor se identifica pela chave do canteiro; sem chave valida, a leitura e recusada. */
    public Leitura registrar(String chaveDispositivo, LeituraRequest pedido) {
        if (chaveDispositivo == null || chaveDispositivo.isBlank()) {
            throw new Erros.ChaveInvalida();
        }
        Canteiro canteiro = canteiros.findByChaveDispositivo(chaveDispositivo.trim())
                .orElseThrow(Erros.ChaveInvalida::new);
        Instant quando = pedido.registradaEm() != null ? pedido.registradaEm() : Instant.now();
        return leituras.save(new Leitura(canteiro, pedido.umidadeSolo(), pedido.temperaturaAr(),
                pedido.luminosidade(), quando));
    }

    public List<Leitura> ultimas(Long canteiroId, int limite) {
        int tamanho = Math.max(1, Math.min(limite, 500));
        return leituras.findByCanteiroIdOrderByRegistradaEmDesc(canteiroId, PageRequest.of(0, tamanho));
    }

    public Leitura ultimaOuNulo(Long canteiroId) {
        return leituras.findFirstByCanteiroIdOrderByRegistradaEmDesc(canteiroId).orElse(null);
    }

    public List<Leitura> desde(Instant desde) {
        return leituras.findByRegistradaEmAfterOrderByRegistradaEmAsc(desde);
    }
}
