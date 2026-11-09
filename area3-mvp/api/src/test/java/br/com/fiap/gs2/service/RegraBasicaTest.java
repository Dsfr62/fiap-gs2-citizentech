package br.com.fiap.gs2.service;

import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Cultura;
import br.com.fiap.gs2.model.Leitura;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

/** Testes de unidade da regra basica: nao precisam subir a aplicacao. */
class RegraBasicaTest {

    private final Canteiro alface = new Canteiro("Alface", Cultura.FOLHOSA, 120, 30, null, null, "x", null);

    @Test
    @DisplayName("CT12 - solo umido: nao rega")
    void soloUmidoNaoRega() {
        var decisao = RegraBasica.decidir(alface, new Leitura(alface, 60, 25, 50, Instant.now()));
        assertFalse(decisao.regar());
        assertEquals(0, decisao.minutos());
    }

    @Test
    @DisplayName("CT13 - solo seco: rega 32 min (8 mm x 120 m2 = 960 L, a 30 L/min)")
    void soloSecoRega() {
        var decisao = RegraBasica.decidir(alface, new Leitura(alface, 35, 24, 40, Instant.now()));
        assertTrue(decisao.regar());
        assertEquals(960, decisao.litros());
        assertEquals(32, decisao.minutos());
    }

    @Test
    @DisplayName("CT14 - dia quente e de sol soma 1 mm (com deficit pequeno, sem bater no teto)")
    void diaQuenteSomaUmMilimetro() {
        var frio = RegraBasica.decidir(alface, new Leitura(alface, 44, 22, 30, Instant.now()));
        var quente = RegraBasica.decidir(alface, new Leitura(alface, 44, 33, 90, Instant.now()));
        assertEquals(frio.litros() + 120, quente.litros());
    }
}
