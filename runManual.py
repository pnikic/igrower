# -*- coding: utf-8 -*-

from controls import Controls

# Rucno pokretanje motora
C = Controls("/dev/ttyACM0")

C.Move(0, 'M', 10)

C.Close()

# Motor 0: + je prema glavnoj stazi
# Motor 1: + je prema gore
# Motor 2: + je u smjeru kazaljke na satu
# Motor 3: + je prema dolje
