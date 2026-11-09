package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.RegaRequest;
import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Rega;
import br.com.fiap.gs2.repository.RegaRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class RegaService {

    private final RegaRepository regas;

    public RegaService(RegaRepository regas) {
        this.regas = regas;
    }

    public Rega registrar(Canteiro canteiro, RegaRequest pedido) {
        double litros = Math.round(pedido.minutos() * canteiro.getVazaoLitrosMin());
        boolean seguiu = pedido.seguiuRecomendacao() != null && pedido.seguiuRecomendacao();
        return regas.save(new Rega(canteiro, Instant.now(), pedido.minutos(), litros, seguiu));
    }

    public List<Rega> listar(Long canteiroId) {
        return regas.findByCanteiroIdOrderByFeitaEmDesc(canteiroId);
    }
}
