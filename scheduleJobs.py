#######################################
# USAGE:
# cd /Path/to/this/file
# python scheduleJobs.py > output.txt
#######################################

import schedule
import time
import datetime
import runSystem

# Global variables
s1 = '5:00:00' # start date

sun = open('sunrises_copy.txt', 'r')
sunrises = [x.split()[1] for x in sun.readlines()]
sun.close()
# End

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
    global sunrises, s1
    s2 = sunrises[todayDecimal()]
    
    FMT = '%H:%M:%S'
    print("Now:", datetime.datetime.now(), "\nWaiting for sunrise...", s2, flush=True)
    td = datetime.datetime.strptime(s2, FMT) - datetime.datetime.strptime(s1, FMT)
    secs = timedelta2seconds(td)
    time.sleep(secs)
    print("It's sunrise. Work started...", datetime.datetime.now(), flush=True)
    runSystem.run()

temp_job_times = ['4:00', '20:28']

def temp_job():
    print("Job started...", datetime.datetime.now(), flush=True)
    runSystem.run()
    print("Job ended...", datetime.datetime.now(), flush=True)

################################ MAIN PROGRAM ################################
if __name__ == "__main__": 
    print("Getting ready to start jobs... (%s)" % datetime.datetime.now(), flush=True)
    #schedule.every().day.at(s1[:-3:]).do(sunrise_job)
    for temp_time in temp_job_times:
        schedule.every().day.at(temp_time).do(temp_job)
    
    flag = True
    while flag:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(str(e), flush=True)
            print("Jobs shut down...(%s)" % datetime.datetime.now(), flush=True)
            flag = False
##############################################################################
