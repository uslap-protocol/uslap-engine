#!/usr/bin/env python3
"""
Flat unwrapped lower body — CLEAN SYMMETRICAL UPRIGHT.
No rotation. Perfectly symmetric about x=0.
Right gore to the right, left gore to the left.
Y = height (up). X = horizontal. Z = 0 (flat).

Gore = 270° strip. Cut at spine (0°) AND axial line (270°).
  LEFT edge of right gore = axial line (inner)
  RIGHT edge of right gore = spine (outer)

Crotch gap centered on x=0.
"""
import math, os

PI = math.pi

def lerp(a, b, t):
    return a + (b - a) * t

PROFILE = [
    (0.080, 0.035, 0.200, 0.000),
    (0.150, 0.040, 0.200, 0.000),
    (0.250, 0.048, 0.200, 0.000),
    (0.350, 0.055, 0.200, 0.000),
    (0.450, 0.050, 0.200, 0.000),
    (0.500, 0.055, 0.200, 0.000),
    (0.600, 0.070, 0.200, 0.000),
    (0.700, 0.080, 0.200, 0.008),
    (0.780, 0.085, 0.200, 0.025),
    (0.830, 0.090, 0.195, 0.060),
    (0.870, 0.095, 0.150, 0.065),
    (0.910, 0.100, 0.100, 0.055),
    (0.955, 0.105, 0.050, 0.035),
    (1.000, 0.100, 0.000, 0.015),
    (1.045, 0.098, 0.000, 0.005),
    (1.085, 0.100, 0.000, 0.000),
    (1.125, 0.105, 0.000, 0.000),
]

def prof_at(y):
    if y <= PROFILE[0][0]: return PROFILE[0]
    if y >= PROFILE[-1][0]: return PROFILE[-1]
    for i in range(len(PROFILE) - 1):
        y0, r0, s0, g0 = PROFILE[i]
        y1, r1, s1, g1 = PROFILE[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0) if y1 != y0 else 0
            return (y, lerp(r0, r1, t), lerp(s0, s1, t), lerp(g0, g1, t))
    return PROFILE[-1]

def interp_kf(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    if t >= kf[-1][0]: return kf[-1][1]
    for i in range(len(kf) - 1):
        t0, a0 = kf[i]; t1, a1 = kf[i + 1]
        if t0 <= t <= t1:
            return lerp(a0, a1, (t - t0) / (t1 - t0) if t1 != t0 else 0)
    return kf[-1][1]

# 270° strip: cut at 270° (axial) AND 0° (spine)
# Seam (270°) at LEFT, spine (0°) at RIGHT
def angle_to_x(raw_deg, radius, offset):
    dist = (270.0 - raw_deg) % 360.0
    if dist > 270.0: dist = 270.0
    frac = dist / 270.0  # 0=seam(left), 1=spine(right)
    return offset + radius * 1.5 * PI * (frac - 0.5)

L1_KF = [(0,0),(.14,15),(.29,40),(.43,80),(.57,130),(.71,175),(.86,220),(.93,250),(1,270)]
L2_KF = [(0,0),(.06,15),(.14,40),(.23,80),(.34,130),(.49,170),(.57,195),(.71,220),(.86,250),(1,270)]
L3_KF = [(0,0),(.08,20),(.15,50),(.25,90),(.38,130),(.50,155),(.58,175),(.70,210),(.83,240),(.93,260),(1,270)]
L4_KF = [(0,0),(.04,15),(.10,40),(.18,70),(.28,105),(.38,135),(.48,160),(.55,175),(.62,195),(.72,210),(.82,215),(.92,218),(1,220)]
L5_KF = [(0,0),(.01,30),(.02,60),(.03,85),(.04,90),(.20,90),(.40,90),(.60,92),(.80,97),(.90,102),(1,105)]
S1_KF = [(0,0),(.05,10),(.12,22),(.22,36),(.35,46),(.50,53),(.65,58),(.78,61),(.90,63),(1,65)]
S2_KF = [(0,0),(.06,6),(.15,12),(.28,15),(.42,12),(.56,3),(.68,-15),(.78,-35),(.88,-60),(1,-90)]
SEAM_KF = [(0,270),(1,270)]

T11_Y=1.125; BB_Y=1.085; PB_Y=0.830

DERMATOMES = [
    dict(label='L1', color='lt_blue', sy=1.045, bot=0.78, kf=L1_KF),
    dict(label='L2', color='lt_blue', sy=1.000, bot=0.55, kf=L2_KF),
    dict(label='L3', color='red_dot', sy=0.955, bot=0.48, kf=L3_KF),
    dict(label='L4', color='yellow',  sy=0.910, bot=0.08, kf=L4_KF, toe=0),
    dict(label='L5', color='warp',    sy=0.870, bot=0.08, kf=L5_KF, toe=2),
    dict(label='S1', color='pink',    sy=0.830, bot=0.08, kf=S1_KF, toe=4),
    dict(label='S2', color='blue_dot',sy=0.800, bot=0.48, kf=S2_KF),
    dict(label='SEAM',color='red',    sy=0.870, bot=0.04, kf=SEAM_KF),
]
TOES = [
    dict(name='BigToe',angle=210,w=0.012,l=0.040),
    dict(name='Toe2',  angle=190,w=0.008,l=0.035),
    dict(name='Toe3',  angle=170,w=0.008,l=0.032),
    dict(name='Toe4',  angle=145,w=0.007,l=0.028),
    dict(name='LitToe',angle=115,w=0.006,l=0.022),
]
VERTS_LIST = [
    ('T11',1.125),('T12',1.085),('L1',1.045),('L2',1.000),('L3',0.955),
    ('L4',0.910),('L5',0.870),('S1',0.830),('S2',0.800),('S3',0.780),
    ('S4',0.765),('S5',0.755),('Co',0.745),
]

def top_edge_y(deg):
    a = deg % 360.0
    if a <= 180: return lerp(T11_Y, BB_Y, (a/180)**2)
    elif a <= 270: return lerp(BB_Y, PB_Y, (a-180)/90)
    else: return lerp(PB_Y, T11_Y, ((a-270)/90)**2)


def write_flat(path):
    V = []  # vertices
    ring_n = 64
    GAP = 0.10; SPLAY = 13.0; MR = 0.105
    AY = 0.080; FL = 0.22

    def off(y):
        b = 0.75*PI*MR + GAP/2
        return b if y >= PB_Y else b + (PB_Y-y)*math.tan(math.radians(SPLAY))

    def fx(deg, y):
        _, r, _, g = prof_at(y)
        er = r + g * max(0, math.cos(deg*PI/180))**2 * 0.3
        return angle_to_x(deg, er, off(y))

    # Right gore: x_raw as-is. Left gore: mirror about x=0.
    def aR(x_raw, y, z=0):
        V.append((x_raw, y, z)); return len(V)-1
    def aL(x_raw, y, z=0):
        V.append((-x_raw, y, z)); return len(V)-1

    # ── BODY RINGS ──
    ys = sorted([i/200.0 for i in range(16, int(T11_Y*200)+2, 2)], reverse=True)
    RR, RA, LR, LA = [], [], [], []
    for y in ys:
        rR,aR_,rL,aL_ = [],[],[],[]
        for i in range(ring_n+1):
            d = 360.0*i/ring_n
            ab = y > top_edge_y(d)+0.001
            x = fx(d, y)
            rR.append(aR(x,y)); aR_.append(ab)
            rL.append(aL(x,y)); aL_.append(ab)
        RR.append(rR); RA.append(aR_); LR.append(rL); LA.append(aL_)

    # ── FEET ──
    fo = off(AY)
    RF, LF_ = [], []
    for fi in range(11):
        fr=fi/10.0
        fw = lerp(0.035,0.050,fr/0.6) if fr<0.6 else lerp(0.050,0.025,(fr-0.6)/0.4)
        fy = AY - fr*FL
        rR, rL = [], []
        for i in range(ring_n+1):
            rv = 2*PI*i/ring_n
            x = fo + fw*(rv-PI)
            rR.append(aR(x,fy)); rL.append(aL(x,fy))
        RF.append(rR); LF_.append(rL)

    # ── TOES ──
    tby = AY-FL; bw=0.025
    RTD, LTD = [], []
    for toe in TOES:
        tcx = angle_to_x(toe['angle'], bw, fo)
        tR, tL = [], []
        for ti in range(7):
            tf=ti/6.0; ty=tby-tf*toe['l']
            tw=lerp(toe['w'],toe['w']*0.4,tf)
            rR, rL = [], []
            for vi in range(5):
                vf=vi/4.0; x=tcx+(vf-0.5)*tw*2
                rR.append(aR(x,ty)); rL.append(aL(x,ty))
            tR.append(rR); tL.append(rL)
        RTD.append((toe['name'],tR)); LTD.append((toe['name'],tL))

    # ── LANDMARKS ──
    MS=0.008; VS_=0.006
    # T11
    t11x=fx(0,T11_Y); t11s=len(V)
    for dx,dy in [(MS,0),(0,MS),(-MS,0),(0,-MS),(MS,0)]: V.append((t11x+dx,T11_Y+dy,0.005))
    t11e=len(V)-1
    # BB
    bbx=fx(180,BB_Y); bbs=len(V)
    for dx,dy in [(MS,0),(0,MS),(-MS,0),(0,-MS),(MS,0)]: V.append((bbx+dx,BB_Y+dy,0.005))
    bbe=len(V)-1
    # PB
    pbx=fx(270,PB_Y); pbs=len(V)
    for dx,dy in [(MS,0),(0,MS),(-MS,0),(0,-MS),(MS,0)]: V.append((pbx+dx,PB_Y+dy,0.005))
    pbe=len(V)-1

    # ── VERTEBRAE (both gores) ──
    vmR, vmL = [], []
    spRs=len(V)
    for _,vy in VERTS_LIST: V.append((fx(0,vy),vy,0.005))
    spRe=len(V)-1
    for vn,vy in VERTS_LIST:
        sx=fx(0,vy); ds=len(V)
        for dx,dy in [(VS_,0),(0,VS_),(-VS_,0),(0,-VS_),(VS_,0)]: V.append((sx+dx,vy+dy,0.005))
        vmR.append((vn,ds,len(V)-1))
    spLs=len(V)
    for _,vy in VERTS_LIST: V.append((-fx(0,vy),vy,0.005))
    spLe=len(V)-1
    for vn,vy in VERTS_LIST:
        sx=fx(0,vy); ds=len(V)
        for dx,dy in [(VS_,0),(0,VS_),(-VS_,0),(0,-VS_),(VS_,0)]: V.append((-sx+dx,vy+dy,0.005))
        vmL.append((vn,ds,len(V)-1))

    # ── TOP EDGE ──
    teRs=len(V)
    for i in range(ring_n+1):
        d=360.0*i/ring_n; y=top_edge_y(d); V.append((fx(d,y),y,0.003))
    teRe=len(V)-1
    teLs=len(V)
    for i in range(ring_n+1):
        d=360.0*i/ring_n; y=top_edge_y(d); V.append((-fx(d,y),y,0.003))
    teLe=len(V)-1

    # ── WARP (L5) on both gores ──
    wpRs=len(V)
    for s in range(101):
        t=s/100.0; y=lerp(0.870,0.08,t); a=interp_kf(L5_KF,t)%360
        V.append((fx(a,y),y,0.006))
    wpRe=len(V)-1
    wpLs=len(V)
    for s in range(101):
        t=s/100.0; y=lerp(0.870,0.08,t); a=interp_kf(L5_KF,t)%360
        V.append((-fx(a,y),y,0.006))
    wpLe=len(V)-1

    # ── DERMATOME LINES ──
    MJ=0.15
    dlines=[]
    for d in DERMATOMES:
        for sfn, suf in [(lambda x:x,''), (lambda x:-x,'_L')]:
            segs=[[]]
            px=None
            for s in range(201):
                t=s/200.0; y=lerp(d['sy'],d['bot'],t)
                a=interp_kf(d['kf'],t)%360
                x=sfn(fx(a,y))
                if px is not None and abs(x-px)>MJ: segs.append([])
                V.append((x,y,0.002)); segs[-1].append(len(V)-1); px=x
            if 'toe' in d:
                toe=TOES[d['toe']]
                tx=sfn(angle_to_x(toe['angle'],bw,fo))
                ty_=tby-toe['l']
                lx,ly=V[-1][0],V[-1][1]
                for ts in range(1,11):
                    tf=ts/10.0; V.append((lerp(lx,tx,tf),lerp(ly,ty_,tf),0.002))
                    segs[-1].append(len(V)-1)
            dlines.append((d['label']+suf, d['color'], segs))

    # ═══════════════════════════════════════
    # WRITE OBJ
    # ═══════════════════════════════════════
    mtl = os.path.basename(path).replace('.obj','.mtl')
    with open(path,'w') as f:
        f.write(f"# Flat Lower Body — Symmetrical Upright\n")
        f.write(f"# Verts: {len(V)}\nmtllib {mtl}\n\n")
        # X=horizontal, Y=vertical(up), Z=0 (flat, facing camera)
        for v in V: f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        # Normal pointing toward camera (+Z) so viewer knows the front
        f.write("vn 0 0 1\n")

        def wf(rings,above,name,mat,rev=False):
            f.write(f"\ng {name}\nusemtl {mat}\n")
            for ri in range(len(rings)-1):
                r0,r1=rings[ri],rings[ri+1]; a0,a1=above[ri],above[ri+1]
                for j in range(min(len(r0),len(r1))-1):
                    if a0[j] and a0[j+1] and a1[j] and a1[j+1]: continue
                    if rev: f.write(f"f {r0[j]+1} {r1[j]+1} {r1[j+1]+1} {r0[j+1]+1}\n")
                    else:   f.write(f"f {r0[j]+1}//1 {r0[j+1]+1}//1 {r1[j+1]+1}//1 {r1[j]+1}//1\n")
        def wr(rings,name,mat,rev=False):
            f.write(f"\ng {name}\nusemtl {mat}\n")
            for ri in range(len(rings)-1):
                r0,r1=rings[ri],rings[ri+1]
                for j in range(min(len(r0),len(r1))-1):
                    if rev: f.write(f"f {r0[j]+1} {r1[j]+1} {r1[j+1]+1} {r0[j+1]+1}\n")
                    else:   f.write(f"f {r0[j]+1}//1 {r0[j+1]+1}//1 {r1[j+1]+1}//1 {r1[j]+1}//1\n")

        wf(RR,RA,'R_Leg','skin')
        if RR and RF:
            f.write("\ng R_Ank\nusemtl skin\n")
            r0,r1=RR[-1],RF[0]
            for j in range(min(len(r0),len(r1))-1): f.write(f"f {r0[j]+1}//1 {r0[j+1]+1}//1 {r1[j+1]+1}//1 {r1[j]+1}//1\n")
        wr(RF,'R_Ft','skin')
        for tn,tr in RTD:
            f.write(f"\ng RT_{tn}\nusemtl toe\n")
            for ri in range(len(tr)-1):
                r0,r1=tr[ri],tr[ri+1]
                for j in range(len(r0)-1): f.write(f"f {r0[j]+1}//1 {r0[j+1]+1}//1 {r1[j+1]+1}//1 {r1[j]+1}//1\n")

        wf(LR,LA,'L_Leg','skin',rev=True)
        if LR and LF_:
            f.write("\ng L_Ank\nusemtl skin\n")
            r0,r1=LR[-1],LF_[0]
            for j in range(min(len(r0),len(r1))-1): f.write(f"f {r0[j]+1} {r1[j]+1} {r1[j+1]+1} {r0[j+1]+1}\n")
        wr(LF_,'L_Ft','skin',rev=True)
        for tn,tr in LTD:
            f.write(f"\ng LT_{tn}\nusemtl toe\n")
            for ri in range(len(tr)-1):
                r0,r1=tr[ri],tr[ri+1]
                for j in range(len(r0)-1): f.write(f"f {r0[j]+1} {r1[j]+1} {r1[j+1]+1} {r0[j+1]+1}\n")

        f.write("\n# LANDMARKS\n")
        f.write(f"g T11\nusemtl m_t11\nl "+" ".join(str(i+1) for i in range(t11s,t11e+1))+"\n")
        f.write(f"\ng BB\nusemtl m_bb\nl "+" ".join(str(i+1) for i in range(bbs,bbe+1))+"\n")
        f.write(f"\ng PB\nusemtl m_pb\nl "+" ".join(str(i+1) for i in range(pbs,pbe+1))+"\n")

        f.write("\n# VERTEBRAE\n")
        f.write(f"g SpR\nusemtl sp\nl "+" ".join(str(i+1) for i in range(spRs,spRe+1))+"\n")
        for vn,ds,de in vmR: f.write(f"\ng VR_{vn}\nusemtl sp\nl "+" ".join(str(i+1) for i in range(ds,de+1))+"\n")
        f.write(f"\ng SpL\nusemtl sp\nl "+" ".join(str(i+1) for i in range(spLs,spLe+1))+"\n")
        for vn,ds,de in vmL: f.write(f"\ng VL_{vn}\nusemtl sp\nl "+" ".join(str(i+1) for i in range(ds,de+1))+"\n")

        f.write("\n# TOP EDGE\n")
        f.write(f"g TE_R\nusemtl te\nl "+" ".join(str(i+1) for i in range(teRs,teRe+1))+"\n")
        f.write(f"\ng TE_L\nusemtl te\nl "+" ".join(str(i+1) for i in range(teLs,teLe+1))+"\n")

        f.write("\n# WARP (L5)\n")
        f.write(f"g WP_R\nusemtl warp\nl "+" ".join(str(i+1) for i in range(wpRs,wpRe+1))+"\n")
        f.write(f"\ng WP_L\nusemtl warp\nl "+" ".join(str(i+1) for i in range(wpLs,wpLe+1))+"\n")

        f.write("\n# DERMATOMES\n")
        for label,color,segs in dlines:
            for si,seg in enumerate(segs):
                if len(seg)<2: continue
                sfx=f"_{si}" if len(segs)>1 else ""
                f.write(f"\ng {label}{sfx}\nusemtl {color}\nl "+" ".join(str(i+1) for i in seg)+"\n")

    with open(path.replace('.obj','.mtl'),'w') as f:
        for n,rgb in [
            ('skin',(0.90,0.78,0.65)),('toe',(0.85,0.72,0.58)),
            ('m_t11',(1,0.3,0.3)),('m_bb',(1,0.6,0)),('m_pb',(0.8,0,0.8)),
            ('sp',(0,0.9,0)),('te',(0.8,0.8,0)),
            ('warp',(0,1,0)),
            ('lt_blue',(0.55,0.78,0.95)),('blue_dot',(0.3,0.5,0.9)),
            ('red',(0.95,0.2,0.2)),('red_dot',(0.9,0.35,0.35)),
            ('yellow',(0.95,0.88,0.25)),('pink',(0.95,0.55,0.6)),
        ]:
            f.write(f"newmtl {n}\nKd {rgb[0]:.2f} {rgb[1]:.2f} {rgb[2]:.2f}\n\n")

    print(f"✓ {path}\n  Verts: {len(V)}\n  Open: https://3dviewer.net")


if __name__ == '__main__':
    write_flat(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dermatomes_flat.obj'))
