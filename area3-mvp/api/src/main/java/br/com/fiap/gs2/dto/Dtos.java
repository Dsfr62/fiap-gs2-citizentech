package br.com.fiap.gs2.dto;

import br.com.fiap.gs2.model.*;
import jakarta.validation.constraints.*;

import java.time.Instant;

/**
 * Formatos de entrada e saida da API. As anotacoes de validacao (@NotBlank, @Min, @Max...)
 * barram dado invalido antes de chegar no banco: e uma das praticas de seguranca da Area 4.
 */
public final class Dtos {

    private Dtos() {
    }

    // ---------- autenticacao ----------

    public record LoginRequest(
            @NotBlank @Email String email,
            @NotBlank String senha) {
    }

    public record CadastroRequest(
            @NotBlank @Size(min = 2, max = 120) String nome,
            @NotBlank @Email @Size(max = 160) String email,
            @NotBlank @Size(min = 8, max = 72, message = "a senha precisa ter de 8 a 72 caracteres") String senha) {
    }

    public record TokenResponse(String token, String nome, Papel papel) {
    }

    public record UsuarioResponse(Long id, String nome, String email, Papel papel) {
        public static UsuarioResponse de(Usuario u) {
            return new UsuarioResponse(u.getId(), u.getNome(), u.getEmail(), u.getPapel());
        }
    }

    // ---------- canteiros ----------

    public record CanteiroRequest(
            @NotBlank @Size(max = 80) String nome,
            @NotNull Cultura cultura,
            @NotNull @Positive @Max(100000) Double areaM2,
            @NotNull @Positive @Max(1000) Double vazaoLitrosMin,
            @DecimalMin("-90") @DecimalMax("90") Double latitude,
            @DecimalMin("-180") @DecimalMax("180") Double longitude) {
    }

    public record CanteiroResponse(Long id, String nome, Cultura cultura, double areaM2, double vazaoLitrosMin,
                                   Double latitude, Double longitude, int umidadeMinima, String produtor,
                                   LeituraResponse ultimaLeitura) {
        public static CanteiroResponse de(Canteiro c, Leitura ultima) {
            return new CanteiroResponse(c.getId(), c.getNome(), c.getCultura(), c.getAreaM2(),
                    c.getVazaoLitrosMin(), c.getLatitude(), c.getLongitude(),
                    c.getCultura().getUmidadeMinimaPercentual(), c.getProdutor().getNome(),
                    ultima == null ? null : LeituraResponse.de(ultima));
        }
    }

    /** So volta para quem cria o canteiro: a chave vai para o sensor e nao aparece de novo. */
    public record CanteiroCriadoResponse(CanteiroResponse canteiro, String chaveDispositivo) {
    }

    // ---------- leituras (sensores) ----------

    public record LeituraRequest(
            @NotNull @DecimalMin("0") @DecimalMax("100") Double umidadeSolo,
            @NotNull @DecimalMin("-10") @DecimalMax("60") Double temperaturaAr,
            @NotNull @DecimalMin("0") @DecimalMax("100") Double luminosidade,
            @PastOrPresent Instant registradaEm) {
    }

    public record LeituraResponse(Long id, Long canteiroId, double umidadeSolo, double temperaturaAr,
                                  double luminosidade, Instant registradaEm) {
        public static LeituraResponse de(Leitura l) {
            return new LeituraResponse(l.getId(), l.getCanteiro().getId(), l.getUmidadeSolo(),
                    l.getTemperaturaAr(), l.getLuminosidade(), l.getRegistradaEm());
        }
    }

    // ---------- recomendacao ----------

    public record RecomendacaoResponse(Long id, Long canteiroId, Instant criadaEm, boolean regar, int minutos,
                                       double litros, String explicacao, String origem, double umidadeSoloUsada,
                                       Double chuvaPrevistaMm) {
        public static RecomendacaoResponse de(Recomendacao r) {
            return new RecomendacaoResponse(r.getId(), r.getCanteiro().getId(), r.getCriadaEm(), r.isRegar(),
                    r.getMinutos(), r.getLitros(), r.getExplicacao(), r.getOrigem(), r.getUmidadeSoloUsada(),
                    r.getChuvaPrevistaMm());
        }
    }

    /** O que a API manda para o servico de IA (Area 1). */
    public record PedidoIa(Long canteiroId, String cultura, double areaM2, double vazaoLitrosMin,
                           Double latitude, Double longitude, double umidadeSolo, double temperaturaAr,
                           double luminosidade, int umidadeMinima) {
    }

    /** O que o servico de IA devolve. */
    public record RespostaIa(boolean regar, int minutos, String explicacao, Double chuvaPrevistaMm) {
    }

    // ---------- regas ----------

    public record RegaRequest(
            @NotNull @Min(0) @Max(240) Integer minutos,
            Boolean seguiuRecomendacao) {
    }

    public record RegaResponse(Long id, Long canteiroId, Instant feitaEm, int minutos, double litros,
                               boolean seguiuRecomendacao) {
        public static RegaResponse de(Rega r) {
            return new RegaResponse(r.getId(), r.getCanteiro().getId(), r.getFeitaEm(), r.getMinutos(),
                    r.getLitros(), r.isSeguiuRecomendacao());
        }
    }

    // ---------- erros ----------

    public record ErroResponse(int status, String erro, java.util.Map<String, String> campos) {
    }
}
