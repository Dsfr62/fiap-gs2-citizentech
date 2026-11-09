import { useEffect, useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { api, Canteiro, ErroApi, hora, Leitura, Rega } from '../api';
import { Cartao, Erro, estilos, Topo } from '../componentes';
import { cor } from '../tema';

// Tela 4: o que aconteceu no canteiro: umidade das ultimas 24 leituras e as regas, com a agua gasta.
export function Historico(props: { canteiroId: number; voltar: () => void }) {
  const [canteiro, setCanteiro] = useState<Canteiro | null>(null);
  const [leituras, setLeituras] = useState<Leitura[]>([]);
  const [regas, setRegas] = useState<Rega[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [c, l, r] = await Promise.all([
          api.canteiro(props.canteiroId),
          api.leituras(props.canteiroId, 24),
          api.regas(props.canteiroId),
        ]);
        setCanteiro(c);
        setLeituras([...l].reverse()); // mais antiga primeiro, para ler da esquerda para a direita
        setRegas(r);
      } catch (e) {
        setErro(e instanceof ErroApi ? e.message : 'Não consegui carregar.');
      }
    })();
  }, [props.canteiroId]);

  const seteDias = Date.now() - 7 * 24 * 3600 * 1000;
  const litros7d = regas.filter((r) => new Date(r.feitaEm).getTime() >= seteDias).reduce((t, r) => t + r.litros, 0);
  const seguidas = regas.filter((r) => r.seguiuRecomendacao).length;
  const minimo = canteiro?.umidadeMinima ?? 0;

  return (
    <View style={estilos.tela}>
      <Topo titulo="Histórico" voltar={props.voltar} />
      <ScrollView contentContainerStyle={estilos.conteudo}>
        <Text style={[estilos.texto, { fontWeight: '700', marginBottom: 12 }]}>{canteiro?.nome ?? ''}</Text>

        <Cartao>
          <Text style={estilos.suave}>Umidade do solo · últimas {leituras.length} leituras</Text>
          <View
            accessibilityLabel="Gráfico de barras da umidade do solo"
            style={{ flexDirection: 'row', alignItems: 'flex-end', height: 140, gap: 3, marginTop: 12 }}
          >
            {leituras.map((l) => (
              <View
                key={l.id}
                style={{
                  flex: 1,
                  height: `${Math.max(4, l.umidadeSolo)}%`,
                  backgroundColor: l.umidadeSolo < minimo ? cor.alerta : cor.agua,
                  borderTopLeftRadius: 3,
                  borderTopRightRadius: 3,
                }}
              />
            ))}
          </View>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 }}>
            <Text style={estilos.suave}>{leituras[0] ? hora(leituras[0].registradaEm) : ''}</Text>
            <Text style={estilos.suave}>{leituras.at(-1) ? hora(leituras.at(-1)!.registradaEm) : ''}</Text>
          </View>
          <Text style={[estilos.suave, { marginTop: 8 }]}>Barra laranja: abaixo do mínimo de {minimo}%.</Text>
        </Cartao>

        <View style={{ flexDirection: 'row', gap: 12, marginBottom: 16 }}>
          <Cartao estilo={{ flex: 1, marginBottom: 0 }}>
            <Text style={{ fontSize: 26, fontWeight: '700', color: cor.agua }}>{Math.round(litros7d)} L</Text>
            <Text style={estilos.suave}>água em 7 dias</Text>
          </Cartao>
          <Cartao estilo={{ flex: 1, marginBottom: 0 }}>
            <Text style={{ fontSize: 26, fontWeight: '700', color: cor.verde }}>
              {seguidas}/{regas.length}
            </Text>
            <Text style={estilos.suave}>regas pela recomendação</Text>
          </Cartao>
        </View>

        <Text style={[estilos.texto, { fontWeight: '700', marginBottom: 8 }]}>Regas</Text>
        {regas.length === 0 && <Text style={estilos.suave}>Nenhuma rega registrada.</Text>}
        {regas.map((r) => (
          <Cartao key={r.id} estilo={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <View>
              <Text style={estilos.texto}>{hora(r.feitaEm)}</Text>
              <Text style={estilos.suave}>{r.seguiuRecomendacao ? 'pela recomendação' : 'por conta própria'}</Text>
            </View>
            <View style={{ alignItems: 'flex-end' }}>
              <Text style={[estilos.texto, { fontWeight: '700' }]}>{r.minutos} min</Text>
              <Text style={estilos.suave}>{Math.round(r.litros)} L</Text>
            </View>
          </Cartao>
        ))}
        <Erro mensagem={erro} />
      </ScrollView>
    </View>
  );
}
