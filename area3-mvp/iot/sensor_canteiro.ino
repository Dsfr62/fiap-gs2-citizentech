/*
  Sereno - no de sensores do canteiro (Arduino Uno, simulado no TinkerCad)

  Sensores:
    A0  sensor de umidade do solo (SIG). VCC no pino 7: so liga na hora de ler (o sensor dura mais).
    A1  TMP36, temperatura do ar.
    A2  fotoresistor (LDR) com resistor de 10 kOhm: luz do sol.
  Saida:
    pino 13  LED vermelho: acende quando o solo esta abaixo do minimo. Funciona sem internet,
             o produtor ve o aviso no proprio canteiro.
    Serial   uma linha JSON a cada 2 s, no mesmo formato que a API recebe em POST /api/leituras.
*/

const int PINO_SOLO = A0;
const int PINO_TEMPERATURA = A1;
const int PINO_LUZ = A2;
const int PINO_LIGA_SOLO = 7;
const int PINO_LED_SECO = 13;

const float UMIDADE_MINIMA = 45.0;     // folhosas (alface, couve)
const int SOLO_LEITURA_MAXIMA = 876;  // valor do sensor de umidade no TinkerCad com o solo encharcado
const unsigned long INTERVALO_MS = 2000;

void setup() {
  Serial.begin(9600);
  pinMode(PINO_LIGA_SOLO, OUTPUT);
  pinMode(PINO_LED_SECO, OUTPUT);
  digitalWrite(PINO_LIGA_SOLO, LOW);
}

float lerUmidadeSolo() {
  digitalWrite(PINO_LIGA_SOLO, HIGH);
  delay(10);
  int bruto = analogRead(PINO_SOLO);
  digitalWrite(PINO_LIGA_SOLO, LOW);
  float percentual = (bruto * 100.0) / SOLO_LEITURA_MAXIMA;
  return constrain(percentual, 0, 100);
}

float lerTemperatura() {
  int bruto = analogRead(PINO_TEMPERATURA);
  float volts = bruto * (5.0 / 1024.0);
  return (volts - 0.5) * 100.0;  // TMP36: 10 mV por grau, 0,5 V em 0 grau
}

float lerLuz() {
  int bruto = analogRead(PINO_LUZ);
  return constrain(map(bruto, 0, 1023, 0, 100), 0, 100);
}

void loop() {
  float umidade = lerUmidadeSolo();
  float temperatura = lerTemperatura();
  float luz = lerLuz();

  digitalWrite(PINO_LED_SECO, umidade < UMIDADE_MINIMA ? HIGH : LOW);

  Serial.print("{\"umidadeSolo\":");
  Serial.print(umidade, 1);
  Serial.print(",\"temperaturaAr\":");
  Serial.print(temperatura, 1);
  Serial.print(",\"luminosidade\":");
  Serial.print(luz, 1);
  Serial.println("}");

  delay(INTERVALO_MS);
}
