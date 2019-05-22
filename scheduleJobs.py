# -*- coding: utf-8 -*-

#######################################
# USAGE:
# cd iGrower/igrower/
# python3 scheduleJobs.py > /home/pi/Filakov/output.txt &
#######################################

import schedule
import time
import datetime
import runSystem

def timedelta2seconds(td):
    """ Converts a datetime.timedelta object in format %H:%M:%S to seconds
    """
    L = list(map(int, str(td).split(':')))
    return (L[0] * 60 + L[1]) * 60 + L[2]
    
def todayDecimal():
    """ Returns the current day of the year as a decimal number.
    Return value is in range [0, 365].
    """
    now = datetime.datetime.now()
    return int(now.strftime("%j")) - 1

def sunrise_job():
    """ Function called at a fixed time in the morning.
    Waits until today's sunrise and runs the system afterwards.    
    """

    s1 = '5:00:00'
    sun = open('/home/pi/iGrower/igrower/sunrise_times.txt', 'r')
    sunrises = [x.split()[1] for x in sun.readlines()]
    sun.close()
    s2 = sunrises[todayDecimal()]
    
    FMT = '%H:%M:%S'
    print("Now:", datetime.datetime.now(), "\nWaiting for sunrise...", s2, flush=True)
    td = datetime.datetime.strptime(s2, FMT) - datetime.datetime.strptime(s1, FMT)
    secs = timedelta2seconds(td)
    time.sleep(secs)

    print("It's sunrise. Work started...", datetime.datetime.now(), flush=True)
    runSystem.run()
    print("Job ended...", datetime.datetime.now(), flush=True)

def temp_job():
    print("Job started...", datetime.datetime.now(), flush=True)
    runSystem.run()
    print("Job ended...", datetime.datetime.now(), flush=True)

if __name__ == "__main__":
    sunrise_job()

################################ MAIN PROGRAM ################################
#if __name__ == "__main__":
#    print("Getting ready to start jobs... (%s)" % datetime.datetime.now(), flush=True)
#    schedule.every().day.at('06:00').do(temp_job)
#
#    flag = True
#    while flag:
#        try:
#            schedule.run_pending()
#            time.sleep(60)
#        except Exception as e:
#            print(str(e), flush=True)
#            print("Jobs shut down...(%s)" % datetime.datetime.now(), flush=True)
#            flag = False
##############################################################################
