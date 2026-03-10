//variáveis dos componentes
int led[] = {11, 12, 13};
int botao[] = {2, 3, 4};
int fotoresistor = A0;
// tempo comer, tempo brincar, tempo dormir, enquanto dorme, minuto, 15 segundos
unsigned long intervalo[] = {240000/3L, 180000/3L, 600000/3L, 300000/3L, 60000/3L, 15000/3L};

// Tempos e margens
unsigned long tempo_vida = 0;

// comer
unsigned long tempo_fome = 0;
unsigned long bonificacao = 0;
int margem_fome = 0;

//brincar
unsigned long tempo_brincar = 0;
unsigned long bonificacao_2 = 0;
int margem_brincar = 0;

//dormir
unsigned long tempo_dormir = 0;
unsigned long bonificacao_3 = 0;
int margem_dormir = 0;

//penalizacao
unsigned long tempo_penalizacao = 0;
int penalizacao = 0;

//variaveis do fotoresistor
int leituras[]= {};
int amostras = 6;
int leituraIndex = 0;
int gama_adc = 1023;
int media = 0;
unsigned long ultima_leitura_fotore = 0;

//controles de estado
bool dormir = false;
bool morreu = false;
bool c_ativo = false;
bool d_ativo = false;
bool b_ativo = false;

// Estados dos botões
long debounceDelay = 50;

int bttState = LOW;
int lastbttState = LOW;
long lastDebounceTime = 0;

int bttState_2 = LOW;
int lastbttState_2 = LOW;
long lastDebounceTime_2 = 0;

int bttState_3 = LOW;
int lastbttState_3 = LOW;
long lastDebounceTime_3 = 0;

//programa
void setup() {
  
  randomSeed(analogRead(0));
  
//inicializar os componentes
  for (int i = 0; i < 3; i++) {
    pinMode(led[i], OUTPUT);
    pinMode(botao[i], INPUT_PULLUP);
  }
  
  Serial.begin(9600);
  //gerar os valores das margens
  margem_fome = obterMargemAleatoria();
  margem_dormir = obterMargemAleatoria();
  margem_brincar = obterMargemAleatoria();
  Serial.println("Nova vida criada!!");
  Serial.println("Cuide bem dele!!");
}

void loop() {
  
  //tempo de vida total
  tempo_vida = millis();

  // Lógica do jogo
  if (!morreu){
    if (!dormir) {
      if (millis() - tempo_penalizacao >= intervalo[4]) {
        tempo_penalizacao = millis();
        Serial.print("Penalizacao: ");
        Serial.println(penalizacao);
      }

      if (millis() - ultima_leitura_fotore >= intervalo[4]) {
        ultima_leitura_fotore = millis();
        leituraFotoresistor();

        // Calcula a média dos valores
        if (sizeof(leituras) / sizeof(int) == 6) {
          int soma = 0;
          Serial.println("amostras feitas");
          for (int i = 0; i < amostras; i++) {
            soma += leituras[i];
          }
          media = soma / amostras;
        }
      }

      //Ligar os leds 
      if (millis() - tempo_fome >= (intervalo[0] + margem_fome) && !c_ativo) {
        digitalWrite(led[0], HIGH);
        c_ativo = true;
        bonificacao = millis();
        margem_fome = random(-intervalo[4], intervalo[4]);
      }
      if (millis() - tempo_brincar >= (intervalo[1] + margem_brincar) && !b_ativo) {
        digitalWrite(led[1], HIGH);
        b_ativo = true;
        bonificacao_2 = millis();
        margem_brincar = random(-intervalo[4], intervalo[4]);
      }
      if (!d_ativo && ((millis() - tempo_dormir >= intervalo[2] + margem_dormir) || (!d_ativo && (media > (2 * gama_adc) / 3)))) {
        digitalWrite(led[2], HIGH);
        d_ativo = true;
        bonificacao_3 = millis();
        margem_dormir = random(-intervalo[4], intervalo[4]);
      }

      comer();
      brincar();
      saude();
      //verificar penalizacões
      penalizacao = penalizacao_check(c_ativo, bonificacao, penalizacao, intervalo[4]);
      penalizacao = penalizacao_check(d_ativo, bonificacao_3, penalizacao, intervalo[4]);
      penalizacao = penalizacao_check(b_ativo, bonificacao_2, penalizacao, intervalo[4]);
    }
    sono();
  }
}

void comer() {
  int btt_read = !digitalRead(botao[0]);

  if (btt_read != lastbttState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (btt_read != bttState) {
      bttState = btt_read;
      if (bttState && digitalRead(led[0])) {
        tempo_fome = millis();
        digitalWrite(led[0], LOW);
        if (millis() - bonificacao < intervalo[5] && penalizacao > 0) {
          penalizacao -= 5;
        }
        c_ativo = false;
      }
    }
  }

  lastbttState = btt_read;
}


void brincar()
{

  int btt_read_2 = !digitalRead(botao[1]);

  if (btt_read_2 != lastbttState_2)
  {
    lastDebounceTime_2 = millis();
  }
  if ((millis() - lastDebounceTime_2) > debounceDelay)
  {
    if (btt_read_2 != bttState_2)
    {
      bttState_2 = btt_read_2;
      if (bttState_2 && digitalRead(led[1]))
      {
        tempo_brincar = millis();
        digitalWrite(led[1], LOW);
        if (millis() - bonificacao_2 < intervalo[5] && penalizacao > 0) {
          penalizacao -= 5;
        }
        b_ativo = false;
      }
    }
  }

  lastbttState_2 = btt_read_2;
}


void sono() {
  int btt_read_3 = !digitalRead(botao[2]);
  if (btt_read_3 != lastbttState_3) {
    lastDebounceTime_3 = millis();
  }
  if (millis() - lastDebounceTime_3 > debounceDelay) {
    if (btt_read_3 != bttState_3) {
      bttState_3 = btt_read_3;
      if (bttState_3 && digitalRead(led[2])) {
        tempo_dormir = millis();
        digitalWrite(led[2], LOW);
        if (millis() - bonificacao_3 < intervalo[5] && penalizacao > 0) {
          penalizacao -= 5;
        }
        d_ativo = false;
        c_ativo = false;
        b_ativo = false;
        Serial.println("O Tamagotchi foi dormir!!");

        dormir = true;

        leituraIndex = 0;
        for (int i = 0; i < amostras; i++) {
          leituras[i] = 0;
        }
      }
    }
  }
  
  if (dormir && millis() - tempo_dormir >= intervalo[3]) {
    dormir = false;
    Serial.println("O Tamagotchi acordou!!");
    reset_variaveis();

  }

  lastbttState_3 = btt_read_3;
}


void saude(){
  if (penalizacao >= 25){
    Serial.println("O Tamagotchi morreu!!");
    Serial.println("Tem que cuidar melhor dele!!");
    Serial.print("O seu tempo de vida foi de: ");
    Serial.println(tempo_vida);
  	morreu = true;
    for (int i = 0; i <= 2; i++){
    	digitalWrite(led[i], LOW);
    }
  }
}

// leitura do fotoresistor e adiciona ao array
void leituraFotoresistor()
{
    leituras[leituraIndex] = analogRead(fotoresistor);
    leituraIndex = (leituraIndex + 1) % amostras;
}

// numero aleatorio
long obterMargemAleatoria() {
  return random(-intervalo[4], intervalo[4]);
}

//verifica penalização e aplica
int penalizacao_check(bool ativo, unsigned long &tempo, int penalizacao, unsigned long intervalo) {
  if (ativo){
    if (millis() - tempo >= intervalo) {
    // Adiciona penalização a cada intervalo de tempo
      penalizacao += 5;
      tempo = millis();
    } 
  }
  return penalizacao;
}

void reset_variaveis(){
  tempo_fome = millis();
  tempo_dormir = millis();
  tempo_brincar = millis();
}
