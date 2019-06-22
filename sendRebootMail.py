from sendMail import send_mail
import config
import datetime

sbj = "iGrower: Ponovno pokrenuto računalo"
txt = "(" + str(datetime.datetime.now())[:-7:] + ") RPi-Filakov je ponovno pokrenut."

send_mail(config.mail['username'], config.mail['recipients'], sbj, txt, [],
          config.mail['server'], config.mail['port'],
          config.mail['username'], config.mail['password'], True)