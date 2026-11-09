package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.CanteiroRequest;
import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Usuario;
import br.com.fiap.gs2.repository.CanteiroRepository;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.List;

@Service
public class CanteiroService {

    private static final SecureRandom ALEATORIO = new SecureRandom();

    private final CanteiroRepository canteiros;

    public CanteiroService(CanteiroRepository canteiros) {
        this.canteiros = canteiros;
    }

    /** Produtor ve os proprios canteiros; tecnico ve todos. */
    public List<Canteiro> listar(Usuario usuario) {
        return usuario.isTecnico() ? canteiros.findAll() : canteiros.findByProdutorIdOrderByIdAsc(usuario.getId());
    }

    /**
     * Busca um canteiro que o usuario pode ver. Canteiro de outro produtor responde 404,
     * igual a canteiro inexistente, para nao revelar que ele existe.
     */
    public Canteiro buscarPermitido(Long id, Usuario usuario) {
        Canteiro canteiro = canteiros.findById(id)
                .orElseThrow(() -> new Erros.NaoEncontrado("canteiro não encontrado"));
        if (!usuario.isTecnico() && !canteiro.getProdutor().getId().equals(usuario.getId())) {
            throw new Erros.NaoEncontrado("canteiro não encontrado");
        }
        return canteiro;
    }

    public Canteiro criar(CanteiroRequest pedido, Usuario produtor) {
        return canteiros.save(new Canteiro(pedido.nome().trim(), pedido.cultura(), pedido.areaM2(),
                pedido.vazaoLitrosMin(), pedido.latitude(), pedido.longitude(), novaChave(), produtor));
    }

    /** Chave aleatoria de 32 caracteres para o sensor do canteiro. */
    static String novaChave() {
        byte[] bytes = new byte[16];
        ALEATORIO.nextBytes(bytes);
        return HexFormat.of().formatHex(bytes);
    }
}
