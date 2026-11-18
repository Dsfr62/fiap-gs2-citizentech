package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Recomendacao;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface RecomendacaoRepository extends JpaRepository<Recomendacao, Long> {

    Optional<Recomendacao> findFirstByCanteiroIdOrderByCriadaEmDesc(Long canteiroId);

    /** Exportacao para o pipeline da Area 2: os alertas enviados ao produtor. */
    List<Recomendacao> findByCriadaEmAfterOrderByCriadaEmAsc(Instant desde);
}
