package br.com.fiap.gs2.config;

import br.com.fiap.gs2.model.*;
import br.com.fiap.gs2.repository.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.Random;

/**
 * Dados de demonstracao (so quando o banco esta vazio): Seu Jorge com dois canteiros em Ibiuna (SP),
 * a tecnica Ana da cooperativa, e a produtora Maria (para provar que um produtor nao ve o canteiro do outro).
 * As leituras das ultimas 48 h seguem o dia: o solo seca mais com calor e sol, e sobe depois da rega.
 */
@Component
public class DadosIniciais implements CommandLineRunner {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final UsuarioRepository usuarios;
    private final CanteiroRepository canteiros;
    private final LeituraRepository leituras;
    private final RegaRepository regas;
    private final PasswordEncoder passwordEncoder;
    private final String senhaDemo;

    public DadosIniciais(UsuarioRepository usuarios, CanteiroRepository canteiros, LeituraRepository leituras,
                         RegaRepository regas, PasswordEncoder passwordEncoder,
                         @Value("${demo.senha}") String senhaDemo) {
        this.usuarios = usuarios;
        this.canteiros = canteiros;
        this.leituras = leituras;
        this.regas = regas;
        this.passwordEncoder = passwordEncoder;
        this.senhaDemo = senhaDemo;
    }

    @Override
    public void run(String... args) {
        if (usuarios.count() > 0) {
            return;
        }
        String hash = passwordEncoder.encode(senhaDemo);
        Usuario jorge = usuarios.save(new Usuario("Jorge Almeida", "jorge@exemplo.com", hash, Papel.PRODUTOR));
        usuarios.save(new Usuario("Ana Souza (tecnica)", "ana@exemplo.com", hash, Papel.TECNICO));
        Usuario maria = usuarios.save(new Usuario("Maria Lima", "maria@exemplo.com", hash, Papel.PRODUTOR));

        Canteiro alface = canteiros.save(new Canteiro("Canteiro 1 - Alface", Cultura.FOLHOSA, 120, 30,
                -23.6566, -47.2229, "demo-sensor-alface-0001", jorge));
        Canteiro tomate = canteiros.save(new Canteiro("Canteiro 2 - Tomate", Cultura.FRUTO, 80, 20,
                -23.6570, -47.2235, "demo-sensor-tomate-0002", jorge));
        Canteiro couve = canteiros.save(new Canteiro("Horta da Maria - Couve", Cultura.FOLHOSA, 60, 15,
                -23.5980, -47.1830, "demo-sensor-couve-0003", maria));

        Instant agora = Instant.now().truncatedTo(ChronoUnit.HOURS);
        gerarHistorico(alface, agora, 39, new Random(42));
        gerarHistorico(tomate, agora, 55, new Random(7));
        gerarHistorico(couve, agora, 66, new Random(13));

        // Seu Jorge rega todo dia no mesmo horario, 30 minutos, por habito.
        regas.save(new Rega(alface, agora.minus(Duration.ofHours(24)), 30, 900, false));
        regas.save(new Rega(tomate, agora.minus(Duration.ofHours(24)), 30, 600, false));
    }

    private void gerarHistorico(Canteiro canteiro, Instant agora, double umidadeInicial, Random sorte) {
        double umidade = umidadeInicial;
        for (int h = 48; h >= 0; h--) {
            Instant quando = agora.minus(Duration.ofHours(h));
            int hora = quando.atZone(FUSO).getHour();
            double sol = Math.max(0, Math.sin(Math.PI * (hora - 6) / 12.0)); // 0 a noite, 1 ao meio-dia
            double temperatura = 16 + 13 * sol + sorte.nextGaussian() * 0.6;
            double luz = Math.min(100, Math.max(0, 95 * sol + sorte.nextGaussian() * 3));
            double perda = 0.12 + 0.65 * sol + (temperatura > 28 ? 0.15 : 0);
            umidade = umidade - perda;
            if (h == 24) {
                umidade += 18; // a rega de ontem
            }
            umidade = Math.max(5, Math.min(95, umidade + sorte.nextGaussian() * 0.3));
            leituras.save(new Leitura(canteiro, arredondar(umidade), arredondar(temperatura), arredondar(luz), quando));
        }
    }

    private static double arredondar(double valor) {
        return Math.round(valor * 10) / 10.0;
    }
}
