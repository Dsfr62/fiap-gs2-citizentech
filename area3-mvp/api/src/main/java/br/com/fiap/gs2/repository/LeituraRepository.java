package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Leitura;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface LeituraRepository extends JpaRepository<Leitura, Long> {
    List<Leitura> findByCanteiroIdOrderByRegistradaEmDesc(Long canteiroId, Pageable pageable);
    Optional<Leitura> findFirstByCanteiroIdOrderByRegistradaEmDesc(Long canteiroId);
    List<Leitura> findByRegistradaEmAfterOrderByRegistradaEmAsc(Instant desde);
}
