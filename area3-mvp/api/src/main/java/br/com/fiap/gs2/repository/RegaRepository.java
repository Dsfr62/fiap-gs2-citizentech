package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Rega;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

public interface RegaRepository extends JpaRepository<Rega, Long> {

    List<Rega> findByCanteiroIdOrderByFeitaEmDesc(Long canteiroId);

    /** Exportacao para o pipeline da Area 2: as respostas "fiz" (regas registradas). */
    List<Rega> findByFeitaEmAfterOrderByFeitaEmAsc(Instant desde);
}
