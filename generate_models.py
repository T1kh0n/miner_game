import math
import random

def g(f, p):
    with open(f, 'w') as x:
        for v in p:
            x.write(f"v {v[0]} {v[1]} {v[2]}\n")

def sp(s, n=0.0):
    p = []
    ph = math.pi * (3. - math.sqrt(5.))
    for i in range(s):
        y = 1 - (i / float(s - 1)) * 2
        r = math.sqrt(1 - y * y)
        t = ph * i
        ns = 1.0 + random.uniform(-n, n)
        p.append((math.cos(t) * r * ns, y * ns, math.sin(t) * r * ns))
    return p

def cb(s, sz=1.0):
    p = []
    for _ in range(s):
        for d in range(3):
            for sn in [-1, 1]:
                pt = [random.uniform(-sz, sz) for _ in range(3)]
                pt[d] = sn * sz
                p.append(tuple(pt))
    return p

def gm(s):
    p = []
    for _ in range(s):
        z = random.uniform(-1, 1)
        r = 1 - abs(z)
        a = random.uniform(0, 2 * math.pi)
        p.append((math.cos(a)*r, math.sin(a)*r, z * 0.5))
    return p

def rb(s):
    p = []
    for _ in range(int(s*0.3)):
        u, v = random.uniform(0, 2*math.pi), random.uniform(0, math.pi)
        p.append((math.sin(v)*math.cos(u)*0.5, math.cos(v)*0.5 - 0.7, math.sin(v)*math.sin(u)*0.5))
    for _ in range(int(s*0.7)):
        y = random.uniform(-0.1, 1.3)
        a = random.uniform(0, 2*math.pi)
        p.append((math.cos(a)*0.45, y, math.sin(a)*0.45))
    return p

g("wall.obj", cb(40, 1.0))
g("dirt.obj", cb(15, 0.8))
g("rock.obj", sp(250, 0.4))
g("coin.obj", gm(180))
g("player.obj", rb(300))
