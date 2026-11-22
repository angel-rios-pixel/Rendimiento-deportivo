import sqlite3
from pathlib import Path
import pandas as pd

DB = Path(__file__).resolve().parents[1] / 'data' / 'rendimiento.sqlite3'
KINDS = ['Salto','VBT','CMJ cargado','Monitoreo VBT','Movilidad','Dinamometría']

def connect():
    DB.parent.mkdir(exist_ok=True)
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c

def init():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS athletes (id INTEGER PRIMARY KEY, name TEXT NOT NULL, club TEXT NOT NULL DEFAULT "Independiente", sport TEXT DEFAULT "", objective TEXT DEFAULT "", UNIQUE(name,club))')
        c.execute('''CREATE TABLE IF NOT EXISTS measurements (id INTEGER PRIMARY KEY, athlete_id INTEGER NOT NULL REFERENCES athletes(id) ON DELETE CASCADE, date TEXT NOT NULL, kind TEXT NOT NULL, protocol TEXT NOT NULL, load_kg REAL, value REAL, unit TEXT NOT NULL, contact_s REAL, flight_s REAL, expected_velocity REAL, notes TEXT DEFAULT '', source TEXT DEFAULT 'manual', batch TEXT DEFAULT '', UNIQUE(athlete_id,date,kind,protocol,load_kg,value,unit,contact_s,flight_s,expected_velocity,source,batch))''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_measurements ON measurements(athlete_id,date,kind)')

def athletes():
    with connect() as c:return pd.read_sql_query('SELECT * FROM athletes ORDER BY club,name',c)

def add_athlete(name,club,sport='',objective=''):
    name=name.strip();club=club.strip() or 'Independiente'
    if not name or name.startswith('('):raise ValueError('Indica un nombre real del deportista.')
    with connect() as c:
        c.execute('INSERT OR IGNORE INTO athletes(name,club,sport,objective) VALUES(?,?,?,?)',(name,club,sport,objective))
        return c.execute('SELECT id FROM athletes WHERE name=? AND club=?',(name,club)).fetchone()[0]

def measurements(athlete_id=None):
    with connect() as c:
        if athlete_id is None:return pd.read_sql_query('SELECT m.*,a.name,a.club,a.sport FROM measurements m JOIN athletes a ON a.id=m.athlete_id ORDER BY m.date',c)
        return pd.read_sql_query('SELECT m.*,a.name,a.club,a.sport FROM measurements m JOIN athletes a ON a.id=m.athlete_id WHERE athlete_id=? ORDER BY m.date',c,params=(int(athlete_id),))

def add_measurement(record):
    cols=['athlete_id','date','kind','protocol','load_kg','value','unit','contact_s','flight_s','expected_velocity','notes','source','batch']
    vals=[record.get(k) for k in cols]
    if record.get('value') is None or not pd.notna(record['value']):raise ValueError('Falta el valor de la medición')
    if record.get('kind') not in KINDS:raise ValueError('Protocolo no reconocido')
    with connect() as c:
        c.execute('INSERT INTO measurements('+','.join(cols)+') VALUES('+','.join('?' for _ in cols)+')',vals)

def update_measurement(mid, record):
    allowed=['date','protocol','load_kg','value','unit','contact_s','flight_s','expected_velocity','notes']
    cols=[x for x in allowed if x in record]
    if not cols:return
    with connect() as c:c.execute('UPDATE measurements SET '+','.join(f'{k}=?' for k in cols)+' WHERE id=?',[record[k] for k in cols]+[int(mid)])

def delete_measurement(mid):
    with connect() as c:c.execute('DELETE FROM measurements WHERE id=?',(int(mid),))
