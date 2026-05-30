import os,re,pandas as pd
CSV_FILE="Sony - PlayStation Portable.csv"
ROM_FOLDER=r"J:\SONY Playstation portable\iso"
df=pd.read_csv(CSV_FILE)
mapping=dict(zip(df["Name EN"].astype(str),df["Name CN"].astype(str)))
def norm(s):
 s=re.sub(r'\s*\(UMD Disc \d+\)','',s,flags=re.I)
 s=re.sub(r'\s*\(Disc \d+\)','',s,flags=re.I)
 s=re.sub(r'\s*\(Special Edition\)','',s,flags=re.I)
 s=re.sub(r'\s*\(PSP the Best\)','',s,flags=re.I)
 return s.strip()
for f in os.listdir(ROM_FOLDER):
 p=os.path.join(ROM_FOLDER,f)
 if not os.path.isfile(p): continue
 n,e=os.path.splitext(f)
 if e.lower() not in ['.cso','.iso']: continue
 cn=mapping.get(norm(n))
 if cn:
  np=os.path.join(ROM_FOLDER,cn+e)
  if not os.path.exists(np):
   os.rename(p,np)
   print(f,'->',cn+e)
print('done')
