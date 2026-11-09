import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { api, definirToken, ErroApi } from '../api';
import { Botao, Campo, Cartao, Erro, estilos } from '../componentes';
import { NOME_DO_APP, SUBTITULO } from '../config';
import { cor } from '../tema';

// Tela 1: entrar (ou criar conta). Valida o basico aqui; a API valida de novo (nunca confiar so no app).
export function Entrar({ aoEntrar }: { aoEntrar: (nome: string) => void }) {
  const [modo, setModo] = useState<'entrar' | 'cadastrar'>('entrar');
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('jorge@exemplo.com');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function enviar() {
    setErro(null);
    setAviso(null);
    if (!email.includes('@')) return setErro('Digite um e-mail válido.');
    if (senha.length < (modo === 'cadastrar' ? 8 : 1)) {
      return setErro(modo === 'cadastrar' ? 'A senha precisa ter pelo menos 8 caracteres.' : 'Digite a senha.');
    }
    setCarregando(true);
    try {
      if (modo === 'cadastrar') {
        await api.cadastrar(nome.trim(), email.trim(), senha);
        setModo('entrar');
        setAviso('Conta criada. Agora entre com o seu e-mail e senha.');
      } else {
        const resposta = await api.entrar(email.trim(), senha);
        definirToken(resposta.token);
        aoEntrar(resposta.nome);
      }
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Algo deu errado.');
    } finally {
      setCarregando(false);
    }
  }

  return (
    <ScrollView style={estilos.tela} contentContainerStyle={[estilos.conteudo, { paddingTop: 72 }]}>
      <Text style={estilos.titulo}>{NOME_DO_APP}</Text>
      <Text style={[estilos.subtitulo, { marginBottom: 32 }]}>{SUBTITULO}</Text>
      <Cartao>
        {modo === 'cadastrar' && <Campo rotulo="Seu nome" value={nome} onChangeText={setNome} />}
        <Campo
          rotulo="E-mail"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
        />
        <Campo rotulo="Senha" value={senha} onChangeText={setSenha} secureTextEntry onSubmitEditing={enviar} />
        <Botao titulo={modo === 'entrar' ? 'Entrar' : 'Criar conta'} onPress={enviar} carregando={carregando} />
        <Erro mensagem={erro ?? aviso} />
      </Cartao>
      <Pressable
        accessibilityRole="button"
        onPress={() => {
          setModo(modo === 'entrar' ? 'cadastrar' : 'entrar');
          setErro(null);
        }}
      >
        <Text style={{ color: cor.verde, fontSize: 17, fontWeight: '600', textAlign: 'center' }}>
          {modo === 'entrar' ? 'Não tem conta? Criar conta' : 'Já tenho conta'}
        </Text>
      </Pressable>
      <View style={{ marginTop: 32 }}>
        <Text style={estilos.suave}>Demonstração: jorge@exemplo.com (produtor) ou ana@exemplo.com (técnica), senha horta2026.</Text>
      </View>
    </ScrollView>
  );
}
