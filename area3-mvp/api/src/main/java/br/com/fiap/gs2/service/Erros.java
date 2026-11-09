package br.com.fiap.gs2.service;

/** Erros de negocio que viram codigos HTTP no TratadorDeErros. */
public final class Erros {

    private Erros() {
    }

    /** 404: nao existe ou o usuario nao pode ver (nao contamos qual dos dois). */
    public static class NaoEncontrado extends RuntimeException {
        public NaoEncontrado(String mensagem) { super(mensagem); }
    }

    /** 401: chave do sensor errada. */
    public static class ChaveInvalida extends RuntimeException {
        public ChaveInvalida() { super("chave do dispositivo inválida"); }
    }

    /** 409: pedido valido, mas o estado nao permite (ex.: recomendar sem nenhuma leitura). */
    public static class Conflito extends RuntimeException {
        public Conflito(String mensagem) { super(mensagem); }
    }
}
