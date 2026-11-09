package br.com.fiap.gs2;

import br.com.fiap.gs2.repository.CanteiroRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.greaterThan;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Casos de teste da API (plano completo em docs/plano-de-testes.md).
 * A IA fica desligada (ia.url vazio) para o resultado nao depender de outro servico.
 */
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {"ia.url=", "demo.senha=horta2026"})
class ApiTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ObjectMapper json;

    @Autowired
    private CanteiroRepository canteiros;

    private String token(String email) throws Exception {
        String corpo = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\"" + email + "\",\"senha\":\"horta2026\"}"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return json.readTree(corpo).get("token").asText();
    }

    private Long idDoCanteiro(String chave) {
        return canteiros.findByChaveDispositivo(chave).orElseThrow().getId();
    }

    @Test
    @DisplayName("CT01 - login com senha certa devolve token")
    void loginComSenhaCerta() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\"jorge@exemplo.com\",\"senha\":\"horta2026\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.papel").value("PRODUTOR"));
    }

    @Test
    @DisplayName("CT02 - login com senha errada devolve 401")
    void loginComSenhaErrada() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\"jorge@exemplo.com\",\"senha\":\"errada123\"}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("CT03 - rota protegida sem token devolve 401")
    void semToken() throws Exception {
        mvc.perform(get("/api/canteiros")).andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("CT04 - sensor com chave invalida e recusado (401)")
    void leituraComChaveInvalida() throws Exception {
        mvc.perform(post("/api/leituras").header("X-Chave-Dispositivo", "chave-falsa")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"umidadeSolo\":40,\"temperaturaAr\":25,\"luminosidade\":50}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("CT05 - leitura fora da faixa (umidade 150%) e barrada pela validacao (400)")
    void leituraForaDaFaixa() throws Exception {
        mvc.perform(post("/api/leituras").header("X-Chave-Dispositivo", "demo-sensor-alface-0001")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"umidadeSolo\":150,\"temperaturaAr\":25,\"luminosidade\":50}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.campos.umidadeSolo").exists());
    }

    @Test
    @DisplayName("CT06 - produtor nao ve o canteiro de outro produtor (404)")
    void produtorNaoVeCanteiroDeOutro() throws Exception {
        Long canteiroDaMaria = idDoCanteiro("demo-sensor-couve-0003");
        mvc.perform(get("/api/canteiros/" + canteiroDaMaria)
                        .header("Authorization", "Bearer " + token("jorge@exemplo.com")))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("CT07 - lista do produtor traz so os canteiros dele, com o nome do produtor")
    void listaSoOsProprios() throws Exception {
        mvc.perform(get("/api/canteiros").header("Authorization", "Bearer " + token("jorge@exemplo.com")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].produtor").value("Jorge Almeida"));
        mvc.perform(get("/api/canteiros").header("Authorization", "Bearer " + token("ana@exemplo.com")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(2)));
    }

    @Test
    @DisplayName("CT08 - fluxo completo: leitura seca -> recomendacao (regra basica) -> rega registrada")
    void fluxoCompleto() throws Exception {
        String tokenJorge = token("jorge@exemplo.com");
        Long alface = idDoCanteiro("demo-sensor-alface-0001");

        mvc.perform(post("/api/leituras").header("X-Chave-Dispositivo", "demo-sensor-alface-0001")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"umidadeSolo\":35,\"temperaturaAr\":24,\"luminosidade\":40}"))
                .andExpect(status().isCreated());

        mvc.perform(post("/api/canteiros/" + alface + "/recomendacoes")
                        .header("Authorization", "Bearer " + tokenJorge))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.origem").value("REGRA_BASICA"))
                .andExpect(jsonPath("$.regar").value(true))
                .andExpect(jsonPath("$.minutos").value(32));

        String rega = mvc.perform(post("/api/canteiros/" + alface + "/regas")
                        .header("Authorization", "Bearer " + tokenJorge)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"minutos\":32,\"seguiuRecomendacao\":true}"))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        JsonNode corpo = json.readTree(rega);
        org.junit.jupiter.api.Assertions.assertEquals(960.0, corpo.get("litros").asDouble());

        mvc.perform(get("/api/canteiros/" + alface + "/regas").header("Authorization", "Bearer " + tokenJorge))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(1)));
    }

    @Test
    @DisplayName("CT09 - exportacao para o pipeline: tecnico entra (200), produtor nao (403)")
    void exportacaoSoParaTecnico() throws Exception {
        mvc.perform(get("/api/dados/leituras").header("Authorization", "Bearer " + token("ana@exemplo.com")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(0)));
        mvc.perform(get("/api/dados/leituras").header("Authorization", "Bearer " + token("jorge@exemplo.com")))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("CT10 - cadastro com senha curta e recusado (400)")
    void cadastroComSenhaCurta() throws Exception {
        mvc.perform(post("/api/auth/cadastro").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"nome\":\"Teste\",\"email\":\"teste@exemplo.com\",\"senha\":\"123\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.campos.senha").exists());
    }

    @Test
    @DisplayName("CT11 - monitoramento: /actuator/health responde UP sem login")
    void saude() throws Exception {
        mvc.perform(get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }
}
