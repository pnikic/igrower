def pad2(s):
    return '0' + s if len(s) < 2 else s

def add(stamp, hrs, mins, secs):
    """ Returns modified timestamp with added hours, minutes and seconds """
    
    L = list(map(int, stamp.split(':')))
    s = ((L[0] + hrs) * 60 + L[1] + mins) * 60 + L[2] + secs       
    return str(s // 3600) + ':' + \
        pad2(str((s % 3600) // 60)) + ':' + \
        pad2(str(((s % 3600) % 60)))
        
def update(L, start_ind, end_ind, hrs, mins, secs):
    """ Updates list L of sunrises from start_ind to end_ind (inclusive)
    by adding hours, minutes and seconds to each entry """
    
    M = list(L)
    for i in range(start_ind, end_ind + 1):
        M[i] = add(M[i], hrs, mins, secs)
        
    return M
    
if __name__ == "__main__":
    sun = open('sunrises.txt', 'r')
    sunrises = [x for x in sun.readlines()]
    suns = [x.split()[1] for x in sunrises]
    
    # Primjer: Dodaje 1:00:00 na indeksima [a, b]
    a = 0
    b = 365
    M = update(suns, a, b, 3, 0, 0)
    
    F = open('sunrises_copy.txt', 'w')
    for i in range(len(sunrises)):
        F.write(sunrises[i].split()[0] + ' ' + M[i] +  '\n')
        
    sun.close()
    F.close()
