package br.com.fiap.gs2.repository;

import br.com.fiap.gs2.model.Canteiro;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface CanteiroRepository extends JpaRepository<Canteiro, Long> {
    List<Canteiro> findByProdutorIdOrderByIdAsc(Long produtorId);
    Optional<Canteiro> findByChaveDispositivo(String chaveDispositivo);
}
