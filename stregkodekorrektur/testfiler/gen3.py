# Selvlavede testfiler til tillæg (EAN-2) og X under 0,264 mm. Fiktivt nummer 2000000000015 (prefix 20, begrænset cirkulation).
# UPC-A bruger 020000000003? Nej: UPC-A-nummeret 200000000004 er også begrænset cirkulation (prefix 2).
import json, fitz, zxingcpp, numpy as np
MM=72/25.4
L=["0001101","0011001","0010011","0111101","0100011","0110001","0101111","0111011","0110111","0001011"]
def G(d): return "".join("1" if c=="0" else "0" for c in L[d])[::-1]
def ean2(v):
    a,b=divmod(v,10); par=["LL","LG","GL","GG"][v%4]
    s="1011"+(L[a] if par[0]=="L" else G(a))+"01"+(L[b] if par[1]=="L" else G(b))
    return [c=="1" for c in s]
def bars(pg,mods,ox,oy,X,h):
    i=0
    while i<len(mods):
        if mods[i]:
            j=i
            while j<len(mods) and mods[j]: j+=1
            pg.draw_rect(fitz.Rect((ox+i*X)*MM,oy*MM,(ox+j*X)*MM,(oy+h)*MM),color=None,fill=(0,0,0)); i=j
        else: i+=1
def make(path,fmt,num,X,h,gap_x,addon):
    bm=zxingcpp.write_barcode(fmt,num,width=95 if fmt==zxingcpp.BarcodeFormat.EAN13 else 95,height=1,quiet_zone=0)
    row=np.array(bm)[0]<128
    doc=fitz.open(); pg=doc.new_page(width=120*MM,height=60*MM)
    ox,oy=20.0,10.0
    bars(pg,list(row),ox,oy,X,h)
    gtxt=num
    fs=2.8*MM
    y=(oy+h+5*X+0.5*X+2.2)*MM
    n=len(row)
    if fmt==zxingcpp.BarcodeFormat.EAN13:
        pg.insert_text(fitz.Point((ox-3.5)*MM,y),gtxt[0],fontsize=fs); pg.insert_text(fitz.Point((ox+3*X)*MM,y),gtxt[1:7],fontsize=fs); pg.insert_text(fitz.Point((ox+50*X)*MM,y),gtxt[7:],fontsize=fs)
    else:
        pg.insert_text(fitz.Point((ox-4)*MM,y),gtxt[0],fontsize=fs); pg.insert_text(fitz.Point((ox+10*X)*MM,y),gtxt[1:6],fontsize=fs); pg.insert_text(fitz.Point((ox+53*X)*MM,y),gtxt[6:11],fontsize=fs); pg.insert_text(fitz.Point((ox+n*X+1)*MM,y),gtxt[11],fontsize=fs)
    if addon is not None:
        ax=ox+(n+gap_x)*X
        bars(pg,ean2(addon),ax,oy,X,h-2*X)
        pg.insert_text(fitz.Point(ax*MM,(oy-1)*MM),f"{addon:02d}",fontsize=fs)
    doc.save(path)
cs=[]
E=zxingcpp.BarcodeFormat.EAN13; U=zxingcpp.BarcodeFormat.UPCA
# (fil, format, nummer, X, hoejde, gap i X, tillaeg, forventet)
for fil,fmt,num,X,gap,ad,forv in [
 ("syn3_00.pdf",E,"2000000000015",0.255,None,None,"X 0,255: VURDER (on-demand)"),
 ("syn3_01.pdf",E,"2000000000015",0.240,None,None,"X 0,240: RET"),
 ("syn3_02.pdf",E,"2000000000015",0.330,8,12,"EAN-13 + 2, 8X: INGEN_FUND"),
 ("syn3_03.pdf",E,"2000000000015",0.330,6,12,"EAN-13 + 2, 6X: RET"),
 ("syn3_04.pdf",U,"200000000004",0.330,8,12,"UPC-A + 2, 8X: RET (min 9X)"),
 ("syn3_05.pdf",U,"200000000004",0.330,10,12,"UPC-A + 2, 10X: INGEN_FUND"),
]:
    h=round(69.24*X*1.05,2); make(fil,fmt,num,X,h,gap or 0,ad); cs.append(dict(fil=fil,forventet=forv))
json.dump(cs,open("cases3.json","w"),indent=1,ensure_ascii=False)
