package br.com.fiap.gs2.model;

import jakarta.persistence.*;

import java.time.Instant;

/** Registro de uma rega feita pelo produtor ("reguei"). Fecha o fluxo: medir, recomendar, regar. */
@Entity
@Table(name = "regas")
public class Rega {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "canteiro_id")
    private Canteiro canteiro;

    @Column(name = "feita_em", nullable = false)
    private Instant feitaEm;

    @Column(nullable = false)
    private int minutos;

    @Column(nullable = false)
    private double litros;

    @Column(name = "seguiu_recomendacao", nullable = false)
    private boolean seguiuRecomendacao;

    protected Rega() {
    }

    public Rega(Canteiro canteiro, Instant feitaEm, int minutos, double litros, boolean seguiuRecomendacao) {
        this.canteiro = canteiro;
        this.feitaEm = feitaEm;
        this.minutos = minutos;
        this.litros = litros;
        this.seguiuRecomendacao = seguiuRecomendacao;
    }

    public Long getId() { return id; }
    public Canteiro getCanteiro() { return canteiro; }
    public Instant getFeitaEm() { return feitaEm; }
    public int getMinutos() { return minutos; }
    public double getLitros() { return litros; }
    public boolean isSeguiuRecomendacao() { return seguiuRecomendacao; }
}
