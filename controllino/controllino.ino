// Controllino macros: https://github.com/CONTROLLINO-PLC/CONTROLLINO_Library/blob/master/Controllino.h (Line 140)

#include <AccelStepper.h>

// Horizontalni, vertikalni, kamera, platno
// Za svaki motor se konfigurira (način rada, pull pin, direction pin)
AccelStepper Steppers[4] = {
  AccelStepper(1, 5, 6),
  AccelStepper(1, 7, 6),
  AccelStepper(1, 18, 6),
  AccelStepper(1, 8, 6)
};

long ind = 0;                                   // Indeks aktivnog motora
long Acc[4]   = {800, 1600, 900, 1000};         // Akceleracije motora
long MaxSp[4] = {1200, 800, 300, 1000};         // Maksimalne brzine motora
long lowerCameraSpeed = 10;                     // Sporija brzina za kameru
// NAPOMENA: Promjene brzine i akceleracije unijeti u controls.py 

// Konfiguracija svjetla
int lightsPin = 19;
bool lightsOn = false;

// Zaštita za motore
int metalCheckPin = 16;
// Vrijeme posljednje obavijesti za metal
unsigned long lastMetalWrite = 0;

void setup() {
  Serial.begin(9600);
  pinMode(metalCheckPin, INPUT);

  for (int i = 0; i < 4; i++)
  {
      Steppers[i].setEnablePin(4);
      Steppers[i].setPinsInverted(false, false, true);
      Steppers[i].setMaxSpeed(MaxSp[i]);
      Steppers[i].setAcceleration(Acc[i]);
  }
}

void loop() {
    if (Serial.available() > 0) 
    {
        char C[20];
        int len = Serial.readBytesUntil('#', C, 20);
        String S(C);
          
        if (S[0] == 'M') { // Motor
            // Example commands: 
            // M0S     - Motor 0 Stop
            // M1H     - Motor 1 Ask home position
            // M2M$400 - Motor 2 Move 400 steps
            // M3M$-40 - Motor 3 Move 40 steps in negative direction

            ind = S[1] - '0';  // Running motor
            char com = S[2];   // Command

            Steppers[ind].enableOutputs();
            
            if (com == 'M') {
                int d1 = S.indexOf('$');
                long stepSize = S.substring(d1 + 1).toInt();
                Steppers[ind].move(stepSize);  
            }    
            else if (com == 'S')
                Steppers[ind].stop();
            else if (com == 'H'){
                Serial.print("Home$");
                Serial.println(Steppers[ind].currentPosition());
            }
        }
        else if (S[0] == 'L'){
            lightsOn = S[1] == '1' ? true : false;
        }
        else if (S[0] == 'C'){
            Steppers[2].setMaxSpeed(S[1] == '1' ? MaxSp[2] : lowerCameraSpeed);  
        }
    }

    unsigned long long now = millis();
    if (now - lastMetalWrite >= 500  && digitalRead(metalCheckPin) == HIGH)
    {
        Serial.println("Metal$");
        lastMetalWrite = now;
    }
    
    digitalWrite(lightsPin, lightsOn ? HIGH : LOW);
    Steppers[ind].run();

   if(abs(Steppers[ind].distanceToGo()) < .1)
      Steppers[ind].disableOutputs();
}
