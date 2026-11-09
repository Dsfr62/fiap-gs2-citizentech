import { useCallback, useEffect, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';
import { api, Canteiro, ErroApi, haQuantoTempo, nomeCultura } from '../api';
import { Botao, Erro, estilos, Topo } from '../componentes';
import { cor, raio } from '../tema';

// Tela 2: lista de canteiros com a ultima umidade de cada um e o aviso de "solo seco".
export function Canteiros(props: {
  nomeUsuario: string;
  abrir: (id: number) => void;
  novo: () => void;
  sair: () => void;
}) {
  const [canteiros, setCanteiros] = useState<Canteiro[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizando, setAtualizando] = useState(false);

  const carregar = useCallback(async () => {
    setAtualizando(true);
    try {
      setCanteiros(await api.canteiros());
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Não consegui carregar.');
    } finally {
      setAtualizando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  return (
    <View style={estilos.tela}>
      <Topo titulo="Meus canteiros" acao={{ titulo: 'Sair', onPress: props.sair }} />
      <ScrollView
        contentContainerStyle={estilos.conteudo}
        refreshControl={<RefreshControl refreshing={atualizando} onRefresh={carregar} />}
      >
        <Text style={[estilos.texto, { marginBottom: 16 }]}>Olá, {props.nomeUsuario.split(' ')[0]}.</Text>
        {canteiros?.length === 0 && <Text style={estilos.suave}>Nenhum canteiro ainda. Cadastre o primeiro.</Text>}
        {canteiros?.map((c) => {
          const umidade = c.ultimaLeitura?.umidadeSolo;
          const seco = umidade !== undefined && umidade < c.umidadeMinima;
          return (
            <Pressable
              key={c.id}
              accessibilityRole="button"
              onPress={() => props.abrir(c.id)}
              style={({ pressed }) => [estilos.cartao, { backgroundColor: pressed ? cor.verdeClaro : cor.cartao }]}
            >
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={[estilos.texto, { fontWeight: '700' }]}>{c.nome}</Text>
                  <Text style={estilos.suave}>
                    {nomeCultura[c.cultura]} · {c.areaM2} m²
                  </Text>
                  <Text style={estilos.suave}>
                    {c.ultimaLeitura ? `Leitura ${haQuantoTempo(c.ultimaLeitura.registradaEm)}` : 'Sem leitura do sensor'}
                  </Text>
                </View>
                <View
                  style={{
                    minWidth: 92,
                    paddingVertical: 10,
                    borderRadius: raio,
                    alignItems: 'center',
                    backgroundColor: umidade === undefined ? cor.fundo : seco ? cor.alertaClaro : cor.aguaClara,
                  }}
                >
                  <Text style={{ fontSize: 24, fontWeight: '700', color: seco ? cor.alerta : cor.agua }}>
                    {umidade === undefined ? '--' : `${Math.round(umidade)}%`}
                  </Text>
                  <Text style={{ fontSize: 13, color: seco ? cor.alerta : cor.agua }}>{seco ? 'solo seco' : 'umidade'}</Text>
                </View>
              </View>
            </Pressable>
          );
        })}
        <Erro mensagem={erro} />
        <Botao titulo="Novo canteiro" tipo="secundario" onPress={props.novo} />
      </ScrollView>
    </View>
  );
}
