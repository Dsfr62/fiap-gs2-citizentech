import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { api, Cultura, ErroApi, nomeCultura } from '../api';
import { Botao, Campo, Cartao, Erro, estilos, Topo } from '../componentes';
import { cor, raio } from '../tema';

const CULTURAS: Cultura[] = ['FOLHOSA', 'FRUTO', 'RAIZ'];

// Tela 5: cadastrar um canteiro. Devolve a chave que vai no sensor do canteiro.
export function NovoCanteiro({ voltar }: { voltar: () => void }) {
  const [nome, setNome] = useState('');
  const [cultura, setCultura] = useState<Cultura>('FOLHOSA');
  const [area, setArea] = useState('');
  const [vazao, setVazao] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [chave, setChave] = useState<string | null>(null);

  async function salvar() {
    const areaM2 = Number(area.replace(',', '.'));
    const vazaoLitrosMin = Number(vazao.replace(',', '.'));
    if (!nome.trim()) return setErro('Dê um nome ao canteiro.');
    if (!(areaM2 > 0)) return setErro('Área precisa ser um número maior que zero.');
    if (!(vazaoLitrosMin > 0)) return setErro('Vazão precisa ser um número maior que zero.');
    setCarregando(true);
    try {
      const resposta = await api.criarCanteiro({ nome: nome.trim(), cultura, areaM2, vazaoLitrosMin });
      setChave(resposta.chaveDispositivo);
      setErro(null);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Não consegui salvar.');
    } finally {
      setCarregando(false);
    }
  }

  return (
    <View style={estilos.tela}>
      <Topo titulo="Novo canteiro" voltar={voltar} />
      <ScrollView contentContainerStyle={estilos.conteudo}>
        {chave ? (
          <Cartao estilo={{ backgroundColor: cor.verdeClaro, borderColor: 'transparent' }}>
            <Text style={[estilos.texto, { fontWeight: '700' }]}>Canteiro criado.</Text>
            <Text style={[estilos.texto, { marginTop: 8 }]}>Chave do sensor (configure no aparelho do canteiro):</Text>
            <Text selectable style={{ fontSize: 18, fontFamily: 'monospace', color: cor.texto, marginTop: 8 }}>
              {chave}
            </Text>
            <Text style={[estilos.suave, { marginTop: 8 }]}>Ela só aparece agora. Guarde antes de sair.</Text>
            <Botao titulo="Voltar aos canteiros" onPress={voltar} />
          </Cartao>
        ) : (
          <Cartao>
            <Campo rotulo="Nome" value={nome} onChangeText={setNome} placeholder="Canteiro 3 - Rúcula" />
            <Text style={estilos.rotulo}>Cultura</Text>
            <View style={{ gap: 8, marginBottom: 16 }}>
              {CULTURAS.map((c) => (
                <Pressable
                  key={c}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: cultura === c }}
                  onPress={() => setCultura(c)}
                  style={{
                    borderWidth: 2,
                    borderColor: cultura === c ? cor.verde : cor.borda,
                    backgroundColor: cultura === c ? cor.verdeClaro : cor.cartao,
                    borderRadius: raio,
                    padding: 14,
                  }}
                >
                  <Text style={estilos.texto}>{nomeCultura[c]}</Text>
                </Pressable>
              ))}
            </View>
            <Campo rotulo="Área (m²)" value={area} onChangeText={setArea} keyboardType="decimal-pad" placeholder="100" />
            <Campo
              rotulo="Vazão da irrigação (litros por minuto)"
              value={vazao}
              onChangeText={setVazao}
              keyboardType="decimal-pad"
              placeholder="20"
            />
            <Botao titulo="Salvar canteiro" onPress={salvar} carregando={carregando} />
            <Erro mensagem={erro} />
          </Cartao>
        )}
      </ScrollView>
    </View>
  );
}
