// C++ code
//
int led1 = 12, led2 = 11, led3 = 10,led4 = 9,led5 = 8;
int btt = 7;
int randValue;

int btt_state = LOW;
int last_state = LOW;

long LastDebounceTime = 0;
long DebounceDelay = 50;

long randNumb;

void setup()
{
  Serial.begin(9600);
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT);
  pinMode(led5, OUTPUT);
  pinMode(btt, INPUT_PULLUP);
  LedsLigados();
  randomSeed(analogRead(0));
}

void loop()
{ 
  int btt_read = !digitalRead(btt);
  
  if (btt_read != last_state){
  		LastDebounceTime = millis();
  }
  if ((millis()- LastDebounceTime) > DebounceDelay){
    if(btt_read != btt_state){
      btt_state = btt_read;
      if (btt_state){
        Serial.write('S');
       	randValue = valorGerado();
        gerarNumero(randValue, led5);
      }
    }
  }
  
  last_state = btt_read;
  verificar();
}

void LedsLigados (){
  for (int contador = 8; contador <= 12; contador++){
  	digitalWrite(contador, HIGH);
  }
} 

void gerarNumero(byte randu, byte led) {
  for(int digit = 0; digit < 5; digit++){
  	digitalWrite(led+digit, (randu>>digit)&1);
  }
}

int valorGerado(){
	int randu = random(32);
  	return randu;
}

void verificar(){
	if (Serial.available() > 0){
        int inp = Serial.read();
        if (inp == randValue){
            Serial.write('Y');
          	LedsLigados();
        }
        if (inp != randValue){
          Serial.write('N');
        }
  	}
}