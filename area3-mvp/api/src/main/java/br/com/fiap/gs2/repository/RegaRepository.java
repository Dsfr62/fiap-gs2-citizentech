package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Rega;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RegaRepository extends JpaRepository<Rega, Long> {
    List<Rega> findByCanteiroIdOrderByFeitaEmDesc(Long canteiroId);
}
