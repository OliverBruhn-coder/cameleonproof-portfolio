import sys, random, json
import fitz, zxingcpp, numpy as np
MM=72/25.4
def gtin(prefix12):
    s=sum(int(c)*(3 if i%2==1 else 1) for i,c in enumerate(prefix12))
    return prefix12+str((10-s%10)%10)
G=gtin("200000000001")   # 200-prefix: begraenset cirkulation, ikke tildelt en virksomhed
def make(path, X, hoejde, ox, oy, guard=5.0):
    bm=zxingcpp.write_barcode(zxingcpp.BarcodeFormat.EAN13, G, width=95, height=1, quiet_zone=0)
    row=np.array(bm)[0]
    dark=(row<128)
    doc=fitz.open(); pg=doc.new_page(width=100*MM, height=60*MM)
    # grupper moduler til streger
    i=0
    guards=set(list(range(0,3))+list(range(45,50))+list(range(92,95)))
    while i<95:
        if dark[i]:
            j=i
            while j<95 and dark[j]: j+=1
            # guard-moduler gaar 5X laengere ned
            ext=guard*X if any(k in guards for k in range(i,j)) else 0
            x0=(ox+i*X)*MM; x1=(ox+j*X)*MM
            y0=oy*MM; y1=(oy+hoejde+ext)*MM
            pg.draw_rect(fitz.Rect(x0,y0,x1,y1), color=None, fill=(0,0,0))
            i=j
        else: i+=1
    # cifre (tekst) under koden
    fs=2.8*MM*1.0
    pg.insert_text(fitz.Point((ox-3.5)*MM,(oy+hoejde+guard*X+0.5*X+2.2)*MM), G[0], fontsize=fs, fontname="helv")
    pg.insert_text(fitz.Point((ox+3*X)*MM,(oy+hoejde+guard*X+0.5*X+2.2)*MM), G[1:7], fontsize=fs, fontname="helv")
    pg.insert_text(fitz.Point((ox+50*X)*MM,(oy+hoejde+guard*X+0.5*X+2.2)*MM), G[7:], fontsize=fs, fontname="helv")
    doc.save(path)
random.seed(7)
cases=[]
for n,X in enumerate([0.264,0.264,0.330,0.330,0.330,0.400,0.500,0.660]):
    h=round(69.24*X*random.choice([0.9,1.0,1.0,1.1]),2)
    ox=round(random.uniform(15,22)+random.random()*0.0212,4); oy=round(random.uniform(8,12)+random.random()*0.0212,4)
    p=f"syn_{n:02d}.pdf"; make(p,X,h,ox,oy)
    cases.append(dict(fil=p,X=X,hoejde=h,ox=ox,oy=oy,gtin=G))
json.dump(cases,open("cases.json","w"),indent=1)
print(G, len(cases))
