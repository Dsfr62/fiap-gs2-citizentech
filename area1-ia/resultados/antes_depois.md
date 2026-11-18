# Antes e depois da IA do Sereno

7 canteiros, 60 dias com o clima real de Ibiúna de 01/09 a 30/10/2025 (136 mm de chuva), período que o modelo nunca viu. Gerado por `python avaliar.py`.

## Seguindo sempre o alerta

| Jeito de regar | Água (L) | Economia contra o calendário | Água perdida (L) | Horas com o solo abaixo do mínimo | Alertas | Acerto do alerta |
|---|---:|---:|---:|---:|---:|---:|
| Antes: calendário (30 min/dia) | 279.000 | 0,0% | 146.535 | 0 |  |  |
| Regra básica (só sensor) | 109.915 | 60,6% | 9.379 | 4.967 | 413 | 49,9% |
| Depois: IA (sensor + previsão) | 108.065 | 61,3% | 3.413 | 581 | 413 | 98,3% |

## Com as respostas "1 fiz / 2 não fiz"

Cada produtor segue o alerta da IA com a chance que tem no gerador da Área 2 (de 50% a 90%).

| Medida | Valor |
|---|---:|
| Alertas enviados | 413 |
| Taxa de "fiz" | 75,8% |
| Acerto quando o produtor respondeu "fiz" | 92,7% |
| Acerto quando respondeu "não fiz" | 22,0% |
| Água usada (L) | 125.440 |
| Horas com o solo abaixo do mínimo | 1.921 |

Acerto: na manhã seguinte o solo estava acima do mínimo e a rega do dia não se perdeu (no máximo 10% escorrendo). A "previsão" usada é o clima que de fato aconteceu: previsão de verdade erra, então o ganho real tende a ser um pouco menor.
