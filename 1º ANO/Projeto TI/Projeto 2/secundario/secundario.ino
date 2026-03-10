int led5 = 8;
int btt = 7, btt_2 = 6;
int num = 0;


int btt_state = LOW;
int last_state = LOW;


long LastDebounceTime = 0;
long DebounceDelay = 50;

//variáveis para o segundo botão e seu debounce
int btt2_state = LOW;
int last_state2 = LOW;

long LastDebounceTime2 = 0;
long DebounceDelay2 = 50;


void setup()
{
  Serial.begin(9600);
  //Inicializar todos os leds com um ciclo for
  for(int pin = 8; pin <=12; pin++){
  	pinMode(pin, OUTPUT);
  }
  pinMode(btt, INPUT_PULLUP);
  pinMode(btt_2, INPUT_PULLUP);
  LedsLigados();//Iniciar o programa com os 5 Leds ligados
  randomSeed(analogRead(0)); //para não gerar sequências de números iguais
}

void loop()
{
  int btt_read = !digitalRead(btt);
  int btt2_read = !digitalRead(btt_2);
  
  if (Serial.available() > 0){
  	char inp = Serial.read();
    if (inp == 'S'){ // input recebido indicador de inicio de jogo
      //Fazer piscar os leds 3 vezes para indicar o início do jogo ao utilizador
      for (int cont = 0; cont<3; cont++){ 
        	LedsLigados();
        	delay(500);
        	LedsDesligados();
        	delay(500);
      }
      num = 0;
    }if (inp == 'N'){ //recebe N logo tentativa errada, desliga todos os Leds
    	LedsDesligados();
      	num = 0;//resetar a variavel num para recomeçar a contar
    }if (inp == 'Y'){ // recebe Y logo tentativa certa, liga todos os Leds
    	LedsLigados();
      	num = 0;//resetar a variavel num para recomeçar a contar
    }
  }
  
  if (btt_read != last_state){
  		LastDebounceTime = millis();
  }
  if ((millis()- LastDebounceTime) > DebounceDelay){
    if(btt_read != btt_state){
      btt_state = btt_read;
      if (btt_state){
        num = num + 1; 
        gerarNumero(num, led5);//chamar a função que mostra o número binário nos Leds
      }
    }
  }
  
  last_state = btt_read;
  // chamar a função do botão tentativa
  debounce_btt2();
}

//Função para ligar todos os leds
void LedsLigados (){
  for (int contador = 8; contador <= 12; contador++){
  	digitalWrite(contador, HIGH);
  }
} 


// Função para desligar todos os leds
void LedsDesligados (){
  for (int contador = 8; contador <= 12; contador++){
  	digitalWrite(contador, LOW);
  }
}

//Função que vai contar em binário e ligar o led correspondente 
void gerarNumero(byte num, byte led) {
  for(int digit = 0; digit < 5; digit++){
  	digitalWrite(led+digit, (num>>digit)&1);
  }
}

//Debounce do botão da tentativa e seu funcionamento
void debounce_btt2 (){
	int btt2_read = !digitalRead(btt_2);
  
    if (btt2_read != last_state2){
          LastDebounceTime2 = millis();
    }
    if ((millis()- LastDebounceTime2) > DebounceDelay2){
      if(btt2_read != btt2_state){
        btt2_state = btt2_read;
        if (btt2_state){
          Serial.write(num); //enviar o valor para o arduino mestre para ser comparado
        }
      }
    }

    last_state2 = btt2_read;
}