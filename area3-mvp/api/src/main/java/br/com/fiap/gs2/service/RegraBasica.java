package br.com.fiap.gs2.service;

import br.com.fiap.gs2.model.Canteiro;
import br.com.fiap.gs2.model.Leitura;

/**
 * Regra basica de irrigacao, usada quando o servico de IA (Area 1) nao responde.
 * E o "plano B" para o produtor nunca ficar sem resposta.
 *
 * Conta, em palavras:
 * 1. alvo = umidade minima da cultura + 10 pontos;
 * 2. se o solo esta acima do minimo, nao rega;
 * 3. se esta abaixo, a lamina (mm) = 0,4 mm por ponto que falta ate o alvo, mais 1 mm em dia quente e de sol,
 *    no maximo 8 mm;
 * 4. 1 mm em 1 m2 = 1 litro; minutos = litros / vazao do canteiro.
 */
public final class RegraBasica {

    static final double MM_POR_PONTO = 0.4;
    static final double LAMINA_MAXIMA_MM = 8.0;

    private RegraBasica() {
    }

    public record Decisao(boolean regar, int minutos, double litros, String explicacao) {
    }

    public static Decisao decidir(Canteiro canteiro, Leitura leitura) {
        int minimo = canteiro.getCultura().getUmidadeMinimaPercentual();
        double umidade = leitura.getUmidadeSolo();
        if (umidade >= minimo) {
            return new Decisao(false, 0, 0,
                    String.format("O solo está com %.0f%% de umidade, acima do mínimo de %d%% para %s. Hoje não precisa regar.",
                            umidade, minimo, nomeCultura(canteiro)));
        }
        double alvo = minimo + 10;
        double lamina = (alvo - umidade) * MM_POR_PONTO;
        boolean diaQuenteDeSol = leitura.getTemperaturaAr() >= 30 && leitura.getLuminosidade() >= 70;
        if (diaQuenteDeSol) {
            lamina += 1.0;
        }
        lamina = Math.min(lamina, LAMINA_MAXIMA_MM);
        double litros = Math.round(lamina * canteiro.getAreaM2());
        int minutos = (int) Math.ceil(litros / canteiro.getVazaoLitrosMin());
        String calor = diaQuenteDeSol ? " Dia quente e de sol: somei um pouco mais." : "";
        return new Decisao(true, minutos, litros,
                String.format("O solo está com %.0f%% de umidade, abaixo do mínimo de %d%% para %s. Regue %d minutos (cerca de %.0f litros), de preferência no fim da tarde.%s",
                        umidade, minimo, nomeCultura(canteiro), minutos, litros, calor));
    }

    private static String nomeCultura(Canteiro canteiro) {
        return switch (canteiro.getCultura()) {
            case FOLHOSA -> "folhosas";
            case FRUTO -> "plantas de fruto";
            case RAIZ -> "raizes";
        };
    }
}
