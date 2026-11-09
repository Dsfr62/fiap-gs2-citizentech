import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import { definirToken } from './src/api';
import { Canteiros } from './src/telas/Canteiros';
import { Entrar } from './src/telas/Entrar';
import { Historico } from './src/telas/Historico';
import { Hoje } from './src/telas/Hoje';
import { NovoCanteiro } from './src/telas/NovoCanteiro';

// Navegacao simples por estado: cada valor de "tela" e uma tela do app.
type Tela =
  | { nome: 'entrar' }
  | { nome: 'canteiros' }
  | { nome: 'hoje'; canteiroId: number }
  | { nome: 'historico'; canteiroId: number }
  | { nome: 'novo' };

export default function App() {
  const [tela, setTela] = useState<Tela>({ nome: 'entrar' });
  const [usuario, setUsuario] = useState('');

  const sair = () => {
    definirToken(null);
    setTela({ nome: 'entrar' });
  };

  let conteudo;
  switch (tela.nome) {
    case 'entrar':
      conteudo = (
        <Entrar
          aoEntrar={(nome) => {
            setUsuario(nome);
            setTela({ nome: 'canteiros' });
          }}
        />
      );
      break;
    case 'canteiros':
      conteudo = (
        <Canteiros
          nomeUsuario={usuario}
          abrir={(id) => setTela({ nome: 'hoje', canteiroId: id })}
          novo={() => setTela({ nome: 'novo' })}
          sair={sair}
        />
      );
      break;
    case 'hoje':
      conteudo = (
        <Hoje
          canteiroId={tela.canteiroId}
          voltar={() => setTela({ nome: 'canteiros' })}
          historico={() => setTela({ nome: 'historico', canteiroId: tela.canteiroId })}
        />
      );
      break;
    case 'historico':
      conteudo = <Historico canteiroId={tela.canteiroId} voltar={() => setTela({ nome: 'hoje', canteiroId: tela.canteiroId })} />;
      break;
    case 'novo':
      conteudo = <NovoCanteiro voltar={() => setTela({ nome: 'canteiros' })} />;
      break;
  }

  return (
    <>
      <StatusBar style="light" />
      {conteudo}
    </>
  );
}
