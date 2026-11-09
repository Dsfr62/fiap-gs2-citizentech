package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Recomendacao;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RecomendacaoRepository extends JpaRepository<Recomendacao, Long> {
    Optional<Recomendacao> findFirstByCanteiroIdOrderByCriadaEmDesc(Long canteiroId);
}
