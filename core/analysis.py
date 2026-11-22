import numpy as np
import pandas as pd

def regression(x,y):
    a=np.asarray(x,dtype=float);b=np.asarray(y,dtype=float)
    mask=np.isfinite(a)&np.isfinite(b);a=a[mask];b=b[mask]
    if len(a)<3 or len(np.unique(a))<3:return None
    slope,intercept=np.polyfit(a,b,1)
    pred=slope*a+intercept;sst=np.sum((b-b.mean())**2)
    r2=float(1-np.sum((b-pred)**2)/sst) if sst>0 else float('nan')
    return {'slope':float(slope),'intercept':float(intercept),'r2':r2,'n':len(a),'x_intercept':float(-intercept/slope) if slope!=0 else None}

def percent_change(last,previous):
    if previous is None or pd.isna(previous) or previous==0:return None
    return 100*(last-previous)/abs(previous)

def summary(df):
    if df.empty:return pd.DataFrame()
    rows=[]
    for (kind,protocol,unit),group in df.groupby(['kind','protocol','unit']):
        g=group.sort_values(['date','id']);latest=g.iloc[-1];prev=g.iloc[-2] if len(g)>1 else None
        rows.append({'Prueba':kind,'Protocolo':protocol,'Unidad':unit,'Último':latest['value'],'Anterior':prev['value'] if prev is not None else np.nan,'Cambio %':percent_change(latest['value'],prev['value']) if prev is not None else np.nan,'Mediciones':len(g)})
    return pd.DataFrame(rows)

def interpretation(df):
    if df.empty:return 'No hay evaluaciones disponibles para interpretar.'
    parts=[]
    for _,r in summary(df).iterrows():
        if pd.isna(r['Cambio %']):continue
        direction='aumentó' if r['Cambio %']>0 else 'disminuyó' if r['Cambio %']<0 else 'se mantuvo'
        parts.append(f"{r['Protocolo']} ({r['Prueba']}) {direction} {abs(r['Cambio %']):.1f}% respecto a la medición anterior.")
    return (' '.join(parts[:8]) if parts else 'Solo hay una medición por indicador; todavía no se pueden estimar tendencias.')+' Los cambios son descriptivos y no demuestran por sí solos mejoras, fatiga o significación práctica. Se requiere controlar condiciones de evaluación y variabilidad individual.'
