package br.com.fiap.gs2.model;

import jakarta.persistence.*;

import java.time.Instant;

/** O que a IA (ou a regra basica, se a IA estiver fora do ar) recomendou para o canteiro. */
@Entity
@Table(name = "recomendacoes")
public class Recomendacao {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "canteiro_id")
    private Canteiro canteiro;

    @Column(name = "criada_em", nullable = false)
    private Instant criadaEm;

    @Column(nullable = false)
    private boolean regar;

    @Column(nullable = false)
    private int minutos;

    @Column(nullable = false)
    private double litros;

    @Column(nullable = false, length = 1000)
    private String explicacao;

    /** "IA" quando veio do servico da Area 1; "REGRA_BASICA" quando a IA nao respondeu. */
    @Column(nullable = false, length = 20)
    private String origem;

    @Column(name = "umidade_solo_usada", nullable = false)
    private double umidadeSoloUsada;

    @Column(name = "chuva_prevista_mm")
    private Double chuvaPrevistaMm;

    protected Recomendacao() {
    }

    public Recomendacao(Canteiro canteiro, Instant criadaEm, boolean regar, int minutos, double litros,
                        String explicacao, String origem, double umidadeSoloUsada, Double chuvaPrevistaMm) {
        this.canteiro = canteiro;
        this.criadaEm = criadaEm;
        this.regar = regar;
        this.minutos = minutos;
        this.litros = litros;
        this.explicacao = explicacao;
        this.origem = origem;
        this.umidadeSoloUsada = umidadeSoloUsada;
        this.chuvaPrevistaMm = chuvaPrevistaMm;
    }

    public Long getId() { return id; }
    public Canteiro getCanteiro() { return canteiro; }
    public Instant getCriadaEm() { return criadaEm; }
    public boolean isRegar() { return regar; }
    public int getMinutos() { return minutos; }
    public double getLitros() { return litros; }
    public String getExplicacao() { return explicacao; }
    public String getOrigem() { return origem; }
    public double getUmidadeSoloUsada() { return umidadeSoloUsada; }
    public Double getChuvaPrevistaMm() { return chuvaPrevistaMm; }
}
