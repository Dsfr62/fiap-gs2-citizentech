package br.com.fiap.gs2.model;

import jakarta.persistence.*;

@Entity
@Table(name = "canteiros")
public class Canteiro {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 80)
    private String nome;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Cultura cultura;

    @Column(name = "area_m2", nullable = false)
    private double areaM2;

    /** Vazao da irrigacao do canteiro, em litros por minuto. Converte minutos em litros. */
    @Column(name = "vazao_litros_min", nullable = false)
    private double vazaoLitrosMin;

    private Double latitude;
    private Double longitude;

    /** Chave que o sensor do canteiro manda no cabecalho X-Chave-Dispositivo. */
    @Column(name = "chave_dispositivo", nullable = false, unique = true, length = 64)
    private String chaveDispositivo;

    /** EAGER: a resposta da API mostra o nome do produtor, entao ele sempre vem junto. */
    @ManyToOne(optional = false, fetch = FetchType.EAGER)
    @JoinColumn(name = "produtor_id")
    private Usuario produtor;

    protected Canteiro() {
    }

    public Canteiro(String nome, Cultura cultura, double areaM2, double vazaoLitrosMin,
                    Double latitude, Double longitude, String chaveDispositivo, Usuario produtor) {
        this.nome = nome;
        this.cultura = cultura;
        this.areaM2 = areaM2;
        this.vazaoLitrosMin = vazaoLitrosMin;
        this.latitude = latitude;
        this.longitude = longitude;
        this.chaveDispositivo = chaveDispositivo;
        this.produtor = produtor;
    }

    public Long getId() { return id; }
    public String getNome() { return nome; }
    public Cultura getCultura() { return cultura; }
    public double getAreaM2() { return areaM2; }
    public double getVazaoLitrosMin() { return vazaoLitrosMin; }
    public Double getLatitude() { return latitude; }
    public Double getLongitude() { return longitude; }
    public String getChaveDispositivo() { return chaveDispositivo; }
    public Usuario getProdutor() { return produtor; }
}
