import { useCallback, useEffect, useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { api, Canteiro, ErroApi, haQuantoTempo, Recomendacao } from '../api';
import { Botao, Cartao, Erro, estilos, Topo } from '../componentes';
import { cor, raio } from '../tema';

const ATUALIZAR_A_CADA_MS = 5000;

// Tela 3: o canteiro agora. Mostra o sensor ao vivo, pede a recomendacao e registra a rega.
export function Hoje(props: { canteiroId: number; voltar: () => void; historico: () => void }) {
  const [canteiro, setCanteiro] = useState<Canteiro | null>(null);
  const [recomendacao, setRecomendacao] = useState<Recomendacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [pedindo, setPedindo] = useState(false);
  const [regando, setRegando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const [c, r] = await Promise.all([api.canteiro(props.canteiroId), api.ultimaRecomendacao(props.canteiroId)]);
      setCanteiro(c);
      setRecomendacao(r);
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Não consegui carregar.');
    }
  }, [props.canteiroId]);

  // Atualiza sozinho: quando o sensor (ou o simulador) manda leitura nova, ela aparece aqui.
  useEffect(() => {
    carregar();
    const relogio = setInterval(carregar, ATUALIZAR_A_CADA_MS);
    return () => clearInterval(relogio);
  }, [carregar]);

  async function pedirRecomendacao() {
    setPedindo(true);
    setAviso(null);
    try {
      setRecomendacao(await api.pedirRecomendacao(props.canteiroId));
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Não consegui pedir a recomendação.');
    } finally {
      setPedindo(false);
    }
  }

  async function reguei() {
    if (!recomendacao) return;
    setRegando(true);
    try {
      const rega = await api.registrarRega(props.canteiroId, recomendacao.minutos, true);
      setAviso(`Rega registrada: ${rega.minutos} min, ${Math.round(rega.litros)} litros.`);
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Não consegui registrar a rega.');
    } finally {
      setRegando(false);
    }
  }

  const leitura = canteiro?.ultimaLeitura;
  const seco = leitura && canteiro ? leitura.umidadeSolo < canteiro.umidadeMinima : false;

  return (
    <View style={estilos.tela}>
      <Topo titulo={canteiro?.nome ?? 'Canteiro'} voltar={props.voltar} acao={{ titulo: 'Histórico', onPress: props.historico }} />
      <ScrollView contentContainerStyle={estilos.conteudo}>
        <Text style={[estilos.suave, { marginBottom: 8 }]}>
          {leitura ? `Sensor: leitura ${haQuantoTempo(leitura.registradaEm)} · atualiza sozinho` : 'Esperando o sensor...'}
        </Text>

        <View style={{ flexDirection: 'row', gap: 12, marginBottom: 16 }}>
          <Medida rotulo="Umidade do solo" valor={leitura ? `${Math.round(leitura.umidadeSolo)}%` : '--'} destaque={seco ? 'seco' : 'ok'} />
          <Medida rotulo="Ar" valor={leitura ? `${leitura.temperaturaAr.toFixed(0)}°C` : '--'} />
          <Medida rotulo="Sol" valor={leitura ? `${Math.round(leitura.luminosidade)}%` : '--'} />
        </View>
        {canteiro && (
          <Text style={[estilos.suave, { marginBottom: 16 }]}>
            Mínimo para esta cultura: {canteiro.umidadeMinima}%. {seco ? 'Abaixo do mínimo.' : 'Dentro do esperado.'}
          </Text>
        )}

        <Cartao estilo={{ backgroundColor: recomendacao?.regar ? cor.aguaClara : cor.verdeClaro, borderColor: 'transparent' }}>
          <Text style={estilos.suave}>Recomendação de hoje</Text>
          {recomendacao ? (
            <>
              <Text style={[estilos.titulo, { color: recomendacao.regar ? cor.agua : cor.verde, marginVertical: 6 }]}>
                {recomendacao.regar ? `Regar ${recomendacao.minutos} min` : 'Não precisa regar'}
              </Text>
              {recomendacao.regar && (
                <Text style={[estilos.texto, { fontWeight: '600' }]}>Cerca de {Math.round(recomendacao.litros)} litros</Text>
              )}
              <Text style={[estilos.texto, { marginTop: 8 }]}>{recomendacao.explicacao}</Text>
              <Text style={[estilos.suave, { marginTop: 8 }]}>
                {recomendacao.origem === 'IA' ? 'Feita pela IA' : 'Regra básica (IA fora do ar)'}
                {recomendacao.chuvaPrevistaMm != null ? ` · chuva prevista ${recomendacao.chuvaPrevistaMm} mm` : ''} ·{' '}
                {haQuantoTempo(recomendacao.criadaEm)}
              </Text>
            </>
          ) : (
            <Text style={[estilos.texto, { marginTop: 6 }]}>Ainda sem recomendação. Toque abaixo para pedir.</Text>
          )}
        </Cartao>

        <Botao titulo="Pedir recomendação agora" onPress={pedirRecomendacao} carregando={pedindo} desativado={!leitura} />
        <Botao
          titulo={recomendacao?.regar ? `Reguei ${recomendacao.minutos} min` : 'Reguei'}
          tipo="agua"
          onPress={reguei}
          carregando={regando}
          desativado={!recomendacao?.regar}
        />
        <Erro mensagem={erro ?? aviso} />
      </ScrollView>
    </View>
  );
}

function Medida(props: { rotulo: string; valor: string; destaque?: 'seco' | 'ok' }) {
  const fundo = props.destaque === 'seco' ? cor.alertaClaro : props.destaque === 'ok' ? cor.aguaClara : cor.cartao;
  const corValor = props.destaque === 'seco' ? cor.alerta : props.destaque === 'ok' ? cor.agua : cor.texto;
  return (
    <View style={{ flex: 1, backgroundColor: fundo, borderRadius: raio, padding: 12, borderWidth: 1, borderColor: cor.borda }}>
      <Text style={{ fontSize: 30, fontWeight: '700', color: corValor }}>{props.valor}</Text>
      <Text style={estilos.suave}>{props.rotulo}</Text>
    </View>
  );
}
