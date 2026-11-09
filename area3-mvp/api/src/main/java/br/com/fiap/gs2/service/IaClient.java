package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.PedidoIa;
import br.com.fiap.gs2.dto.Dtos.RespostaIa;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Optional;

/**
 * Chama o servico de IA da Area 1 (POST {IA_URL}/recomendar). Se a IA estiver desligada,
 * demorar mais de 5 segundos ou responder erro, devolve vazio e a API usa a RegraBasica.
 */
@Component
public class IaClient {

    private static final Logger LOG = LoggerFactory.getLogger(IaClient.class);

    private final RestClient cliente;
    private final boolean ligado;

    public IaClient(@Value("${ia.url:}") String url) {
        SimpleClientHttpRequestFactory fabrica = new SimpleClientHttpRequestFactory();
        fabrica.setConnectTimeout(2000);
        fabrica.setReadTimeout(5000);
        this.ligado = url != null && !url.isBlank();
        this.cliente = RestClient.builder().baseUrl(ligado ? url : "http://localhost").requestFactory(fabrica).build();
    }

    public Optional<RespostaIa> recomendar(PedidoIa pedido) {
        if (!ligado) {
            return Optional.empty();
        }
        try {
            RespostaIa resposta = cliente.post().uri("/recomendar")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(pedido)
                    .retrieve()
                    .body(RespostaIa.class);
            return Optional.ofNullable(resposta);
        } catch (Exception e) {
            LOG.warn("IA fora do ar ({}): usando a regra básica", e.getClass().getSimpleName());
            return Optional.empty();
        }
    }
}
