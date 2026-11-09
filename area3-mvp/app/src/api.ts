import { API_URL } from './config';

// Tipos que a API devolve (mesmos nomes dos DTOs em Java).
export type Papel = 'PRODUTOR' | 'TECNICO';
export type Cultura = 'FOLHOSA' | 'FRUTO' | 'RAIZ';

export interface Leitura {
  id: number;
  canteiroId: number;
  umidadeSolo: number;
  temperaturaAr: number;
  luminosidade: number;
  registradaEm: string;
}

export interface Canteiro {
  id: number;
  nome: string;
  cultura: Cultura;
  areaM2: number;
  vazaoLitrosMin: number;
  umidadeMinima: number;
  produtor: string;
  ultimaLeitura: Leitura | null;
}

export interface Recomendacao {
  id: number;
  criadaEm: string;
  regar: boolean;
  minutos: number;
  litros: number;
  explicacao: string;
  origem: 'IA' | 'REGRA_BASICA';
  umidadeSoloUsada: number;
  chuvaPrevistaMm: number | null;
}

export interface Rega {
  id: number;
  feitaEm: string;
  minutos: number;
  litros: number;
  seguiuRecomendacao: boolean;
}

export class ErroApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

// O token do login fica so na memoria do app: fechou, entra de novo.
let token: string | null = null;
export const definirToken = (novo: string | null) => {
  token = novo;
};

async function chamar<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(opcoes.headers ?? {}),
      },
    });
  } catch {
    throw new ErroApi(0, 'Sem conexão com o servidor. Confira se a API está rodando.');
  }
  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      const campos = corpo.campos ? Object.values(corpo.campos).join('; ') : '';
      mensagem = campos ? `${corpo.erro}: ${campos}` : corpo.erro ?? mensagem;
    } catch {
      // resposta sem corpo (ex.: 401 do filtro de seguranca)
      if (resposta.status === 401) mensagem = 'Sessão expirada. Entre de novo.';
    }
    throw new ErroApi(resposta.status, mensagem);
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json();
}

export const api = {
  entrar: (email: string, senha: string) =>
    chamar<{ token: string; nome: string; papel: Papel }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha }),
    }),
  cadastrar: (nome: string, email: string, senha: string) =>
    chamar('/api/auth/cadastro', { method: 'POST', body: JSON.stringify({ nome, email, senha }) }),
  canteiros: () => chamar<Canteiro[]>('/api/canteiros'),
  canteiro: (id: number) => chamar<Canteiro>(`/api/canteiros/${id}`),
  criarCanteiro: (dados: { nome: string; cultura: Cultura; areaM2: number; vazaoLitrosMin: number }) =>
    chamar<{ canteiro: Canteiro; chaveDispositivo: string }>('/api/canteiros', {
      method: 'POST',
      body: JSON.stringify(dados),
    }),
  leituras: (id: number, limite = 24) => chamar<Leitura[]>(`/api/canteiros/${id}/leituras?limite=${limite}`),
  ultimaRecomendacao: async (id: number) => {
    try {
      return await chamar<Recomendacao>(`/api/canteiros/${id}/recomendacoes/ultima`);
    } catch (e) {
      if (e instanceof ErroApi && e.status === 404) return null;
      throw e;
    }
  },
  pedirRecomendacao: (id: number) => chamar<Recomendacao>(`/api/canteiros/${id}/recomendacoes`, { method: 'POST' }),
  regas: (id: number) => chamar<Rega[]>(`/api/canteiros/${id}/regas`),
  registrarRega: (id: number, minutos: number, seguiuRecomendacao: boolean) =>
    chamar<Rega>(`/api/canteiros/${id}/regas`, {
      method: 'POST',
      body: JSON.stringify({ minutos, seguiuRecomendacao }),
    }),
};

export const nomeCultura: Record<Cultura, string> = {
  FOLHOSA: 'Folhosa (alface, couve)',
  FRUTO: 'Fruto (tomate, pimentão)',
  RAIZ: 'Raiz (cenoura, beterraba)',
};

export function haQuantoTempo(iso: string): string {
  const minutos = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutos < 1) return 'agora';
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.round(minutos / 60);
  return horas < 24 ? `há ${horas} h` : `há ${Math.round(horas / 24)} dia(s)`;
}

export function hora(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')} ${String(
    d.getHours(),
  ).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}
