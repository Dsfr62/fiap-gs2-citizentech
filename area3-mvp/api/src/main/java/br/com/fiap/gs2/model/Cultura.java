package br.com.fiap.gs2.model;

/**
 * Tipo de cultura do canteiro. Cada uma tem um limite de umidade do solo
 * abaixo do qual a planta comeca a sofrer (estresse hidrico).
 */
public enum Cultura {
    FOLHOSA(45),  // alface, couve, rucula: raiz curta, sofre cedo
    FRUTO(38),    // tomate, pimentao
    RAIZ(32);     // cenoura, beterraba

    private final int umidadeMinimaPercentual;

    Cultura(int umidadeMinimaPercentual) {
        this.umidadeMinimaPercentual = umidadeMinimaPercentual;
    }

    public int getUmidadeMinimaPercentual() {
        return umidadeMinimaPercentual;
    }
}
