import hashlib
import io
import pandas as pd
from core.db import add_measurement, connect

SHEETS=['Registro Saltos','Registro VBT','Registro CMJ Cargado','Monitoreo diario press VBT ','Monitoreo diario sentadilla VBT']

def number(v):
    try:
        n=float(v)
        return n if pd.notna(n) else None
    except (ValueError,TypeError):return None

def date(v):
    if pd.isna(v):return None
    try:
        if isinstance(v,(int,float)) and 20000<float(v)<100000:return (pd.Timestamp('1899-12-30')+pd.Timedelta(days=float(v))).date().isoformat()
        return pd.to_datetime(v).date().isoformat()
    except (ValueError,TypeError,OverflowError):return None

def extract(file_bytes,athlete_id):
    book=pd.ExcelFile(io.BytesIO(file_bytes));batch=hashlib.sha256(file_bytes).hexdigest()[:16]
    rows=[];warnings=[]
    def put(d,kind,protocol,value,unit,load=None,flight=None,contact=None,expected=None,notes=''):
        if d and value is not None:
            rows.append(dict(athlete_id=athlete_id,date=d,kind=kind,protocol=str(protocol).strip(),value=value,unit=unit,load_kg=load,flight_s=flight,contact_s=contact,expected_velocity=expected,notes=str(notes) if pd.notna(notes) else '',source='excel',batch=batch))
    if 'Registro Saltos' in book.sheet_names:
        df=pd.read_excel(book,sheet_name='Registro Saltos')
        for _,r in df.iterrows():
            d=date(r.iloc[0]);kind=str(r.iloc[1]).strip().upper();h=number(r.iloc[2]);flight=number(r.iloc[3]);contact=number(r.iloc[4]);notes=r.iloc[6] if len(r)>6 else ''
            if kind in ('ABALAKOV','ABK'):kind='ABK'
            if kind in ('SJ','CMJ','ABK','DJ','DROP JUMP'):
                if h is None and flight is not None:h=9.81*flight**2/8*100
                put(d,'Salto',kind,h,'cm',flight=flight,contact=contact,notes=notes)
    if 'Registro VBT' in book.sheet_names:
        df=pd.read_excel(book,sheet_name='Registro VBT')
        for _,r in df.iterrows():
            d=date(r.iloc[0]);exercise=r.iloc[1]
            if pd.isna(exercise):continue
            for j in range(10):
                load=number(r.iloc[2+j]);speed=number(r.iloc[12+j])
                if load is not None and speed is not None:put(d,'VBT',exercise,speed,'m/s',load=load)
    if 'Registro CMJ Cargado' in book.sheet_names:
        df=pd.read_excel(book,sheet_name='Registro CMJ Cargado')
        for _,r in df.iterrows():
            d=date(r.iloc[0]);protocol=r.iloc[1]
            if pd.isna(protocol):continue
            for j in range(8):
                load=number(r.iloc[2+j]);h=number(r.iloc[10+j])
                if load is not None and h is not None:put(d,'CMJ cargado',protocol,h,'cm',load=load)
    for sheet in ('Monitoreo diario press VBT ','Monitoreo diario sentadilla VBT'):
        if sheet not in book.sheet_names:continue
        df=pd.read_excel(book,sheet_name=sheet)
        for _,r in df.iterrows():
            d=date(r.iloc[0]);exercise=r.iloc[1];load=number(r.iloc[2]);speed=number(r.iloc[3]);expected=number(r.iloc[4]);notes=r.iloc[7] if len(r)>7 else ''
            if pd.notna(exercise):put(d,'Monitoreo VBT',exercise,speed,'m/s',load=load,expected=expected,notes=notes)
    for sheet in ('Movilidad ','Dinamométrica','Programación semanal','Anamnesis'):
        if sheet in book.sheet_names:warnings.append(f'{sheet.strip()}: hoja detectada, pendiente de mapeo estructurado; no se importaron valores automáticamente.')
    return rows,warnings

def save_rows(rows):
    saved=0;errors=[]
    for i,r in enumerate(rows):
        try:
            with connect() as c:
                existing=c.execute("SELECT 1 FROM measurements WHERE athlete_id=? AND source='excel' AND batch=? AND date=? AND kind=? AND protocol=? AND value=? AND load_kg IS ? LIMIT 1",(r['athlete_id'],r['batch'],r['date'],r['kind'],r['protocol'],r['value'],r['load_kg'])).fetchone()
            if existing:continue
            add_measurement(r);saved+=1
        except Exception as e:errors.append(f'Fila {i+1}: {e}')
    return saved,errors
