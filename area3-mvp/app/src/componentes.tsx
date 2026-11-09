import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, TextInputProps, View, ViewStyle } from 'react-native';
import { ReactNode } from 'react';
import { cor, espaco, raio } from './tema';

// Pecas reaproveitadas pelas telas. Estados (apertado, carregando) mudam cor, nao tamanho.

export function Botao(props: {
  titulo: string;
  onPress: () => void;
  tipo?: 'principal' | 'agua' | 'secundario';
  carregando?: boolean;
  desativado?: boolean;
}) {
  const { titulo, onPress, tipo = 'principal', carregando, desativado } = props;
  const fundo = tipo === 'principal' ? cor.verde : tipo === 'agua' ? cor.agua : cor.cartao;
  const corTexto = tipo === 'secundario' ? cor.verde : '#FFFFFF';
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={desativado || carregando}
      style={({ pressed }) => [
        estilos.botao,
        { backgroundColor: fundo, opacity: desativado ? 0.5 : pressed ? 0.85 : 1 },
        tipo === 'secundario' && { borderWidth: 2, borderColor: cor.verde },
      ]}
    >
      <View style={estilos.botaoMiolo}>
        {carregando ? (
          <ActivityIndicator color={corTexto} />
        ) : (
          <Text style={[estilos.botaoTexto, { color: corTexto }]}>{titulo}</Text>
        )}
      </View>
    </Pressable>
  );
}

export function Campo(props: TextInputProps & { rotulo: string }) {
  const { rotulo, ...resto } = props;
  return (
    <View style={{ marginBottom: espaco.m }}>
      <Text style={estilos.rotulo}>{rotulo}</Text>
      <TextInput placeholderTextColor={cor.suave} style={estilos.campo} {...resto} />
    </View>
  );
}

export function Cartao({ children, estilo }: { children: ReactNode; estilo?: ViewStyle }) {
  return <View style={[estilos.cartao, estilo]}>{children}</View>;
}

export function Erro({ mensagem }: { mensagem: string | null }) {
  // Espaco reservado: a mensagem aparece sem empurrar a tela.
  return (
    <Text accessibilityLiveRegion="polite" style={[estilos.erro, { opacity: mensagem ? 1 : 0 }]}>
      {mensagem ?? ' '}
    </Text>
  );
}

export function Topo(props: { titulo: string; voltar?: () => void; acao?: { titulo: string; onPress: () => void } }) {
  return (
    <View style={estilos.topo}>
      <View style={{ width: 80 }}>
        {props.voltar && (
          <Pressable accessibilityRole="button" onPress={props.voltar}>
            <Text style={estilos.topoLink}>Voltar</Text>
          </Pressable>
        )}
      </View>
      <Text numberOfLines={1} style={estilos.topoTitulo}>
        {props.titulo}
      </Text>
      <View style={{ width: 80, alignItems: 'flex-end' }}>
        {props.acao && (
          <Pressable accessibilityRole="button" onPress={props.acao.onPress}>
            <Text style={estilos.topoLink}>{props.acao.titulo}</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

export const estilos = StyleSheet.create({
  tela: { flex: 1, backgroundColor: cor.fundo },
  conteudo: { padding: espaco.m, paddingBottom: 48, width: '100%', maxWidth: 560, alignSelf: 'center' },
  titulo: { fontSize: 28, fontWeight: '700', color: cor.texto },
  subtitulo: { fontSize: 17, color: cor.suave, marginTop: 4 },
  texto: { fontSize: 17, color: cor.texto, lineHeight: 24 },
  suave: { fontSize: 15, color: cor.suave },
  rotulo: { fontSize: 15, color: cor.suave, marginBottom: 6 },
  campo: {
    borderWidth: 1.5,
    borderColor: cor.borda,
    backgroundColor: cor.cartao,
    borderRadius: raio,
    paddingHorizontal: 14,
    height: 52,
    fontSize: 18,
    color: cor.texto,
  },
  botao: { borderRadius: raio, height: 56, justifyContent: 'center', marginTop: espaco.p },
  botaoMiolo: { alignItems: 'center', justifyContent: 'center', height: 56 },
  botaoTexto: { fontSize: 18, fontWeight: '700' },
  cartao: {
    backgroundColor: cor.cartao,
    borderRadius: raio,
    padding: espaco.m,
    marginBottom: espaco.m,
    borderWidth: 1,
    borderColor: cor.borda,
  },
  erro: { color: cor.alerta, fontSize: 15, minHeight: 40, marginTop: espaco.p },
  topo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: espaco.m,
    paddingTop: 48,
    paddingBottom: espaco.m,
    backgroundColor: cor.verde,
  },
  topoTitulo: { color: '#FFFFFF', fontSize: 19, fontWeight: '700', flex: 1, textAlign: 'center' },
  topoLink: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
});
