package br.com.fiap.gs2.model;

import jakarta.persistence.*;

import java.time.Instant;

/** Uma leitura dos sensores do canteiro (umidade do solo, temperatura do ar, luz). */
@Entity
@Table(name = "leituras", indexes = @Index(columnList = "canteiro_id, registrada_em"))
public class Leitura {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "canteiro_id")
    private Canteiro canteiro;

    @Column(name = "umidade_solo", nullable = false)
    private double umidadeSolo;

    @Column(name = "temperatura_ar", nullable = false)
    private double temperaturaAr;

    /** Luz relativa, 0 a 100 (fotoresistor). Dia de sol forte = planta perde mais agua. */
    @Column(nullable = false)
    private double luminosidade;

    @Column(name = "registrada_em", nullable = false)
    private Instant registradaEm;

    protected Leitura() {
    }

    public Leitura(Canteiro canteiro, double umidadeSolo, double temperaturaAr,
                   double luminosidade, Instant registradaEm) {
        this.canteiro = canteiro;
        this.umidadeSolo = umidadeSolo;
        this.temperaturaAr = temperaturaAr;
        this.luminosidade = luminosidade;
        this.registradaEm = registradaEm;
    }

    public Long getId() { return id; }
    public Canteiro getCanteiro() { return canteiro; }
    public double getUmidadeSolo() { return umidadeSolo; }
    public double getTemperaturaAr() { return temperaturaAr; }
    public double getLuminosidade() { return luminosidade; }
    public Instant getRegistradaEm() { return registradaEm; }
}
