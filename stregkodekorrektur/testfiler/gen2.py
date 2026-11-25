import sys, random, json
sys.argv=['x']
exec(open('gen.py').read().split("random.seed(7)")[0])
import fitz
def make2(path,X,h,ox,oy,gl,gr):
    make(path,X,h,ox,oy)
    d=fitz.open(path); pg=d[0]
    L=(ox-gl)*MM; R=(ox+95*X+gr)*MM
    pg.draw_rect(fitz.Rect(L-3*MM, oy*MM, L, (oy+h)*MM), color=None, fill=(0,0,0))
    pg.draw_rect(fitz.Rect(R, oy*MM, R+3*MM, (oy+h)*MM), color=None, fill=(0,0,0))
    d.saveIncr() if False else d.save(path+"x"); 
    import os; os.replace(path+"x",path)
random.seed(3)
cs=[]
for n,(gl,gr) in enumerate([(3.0,2.0),(3.5,2.2),(3.6,2.3),(3.7,2.4),(3.63,2.31),(4.5,3.5)]):
    X=0.33; h=22.85
    ox=20+random.random()*0.0212*3; oy=10+random.random()*0.02
    p=f"syn2_{n:02d}.pdf"; make2(p,X,h,ox,oy,gl,gr); cs.append(dict(fil=p,gl=gl,gr=gr))
json.dump(cs,open("cases2.json","w"))
