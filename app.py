import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from core import db
from core.analysis import regression,summary,interpretation
from core.importer import extract,save_rows
from core.report import create_pdf
from core.google_sheets import listar_archivos, listar_pestanas, leer_pestana

st.set_page_config(page_title='Rendimiento Deportivo',page_icon='🏋️',layout='wide')
db.init()
st.markdown('''<style>.block-container{padding-top:1.5rem}div[data-testid="stMetric"]{background:#14283e;color:white;border-radius:12px;padding:14px}div[data-testid="stMetric"] label{color:#cbd5e1}</style>''',unsafe_allow_html=True)
st.title('🏋️ Plataforma de Rendimiento Deportivo')
st.caption('Evaluación, monitorización y análisis longitudinal | Versión 1.0')
page = st.sidebar.radio(
    'Navegación',
    [
        'Panel del deportista',
        'Importar Excel',
        'Google Sheets',
        'Registrar evaluación',
        'Editar evaluaciones',
        'Comparar deportistas',
        'Gestionar deportistas'
    ]
)
a=db.athletes()
# ==========================================
# CONEXIÓN CON GOOGLE SHEETS
# ==========================================

if page == 'Google Sheets':

    st.header("📊 Evaluaciones desde Google Sheets")

    st.write(
        "Consulta las evaluaciones registradas "
        "en tu carpeta de Google Drive."
    )

    if st.button("🔄 Sincronizar Google Sheets"):
        listar_archivos.clear()
        listar_pestanas.clear()
        leer_pestana.clear()
        st.rerun()

    try:
        archivos = listar_archivos()

        if not archivos:
            st.warning(
                "No se encontraron archivos de Google Sheets "
                "en la carpeta configurada."
            )

        else:
            st.success(
                f"Se encontraron {len(archivos)} archivos."
            )

            opciones = {
                archivo["name"]: archivo["id"]
                for archivo in archivos
            }

            nombre = st.selectbox(
                "Selecciona un archivo",
                list(opciones.keys())
            )

            archivo_id = opciones[nombre]

            pestanas = listar_pestanas(archivo_id)

            if pestanas:
                pestana = st.selectbox(
                    "Selecciona una pestaña",
                    pestanas
                )

                datos = leer_pestana(
                    archivo_id,
                    pestana
                )

                st.subheader("Resultados registrados")

                st.dataframe(
                    datos,
                    use_container_width=True
                )

                st.write(
                    f"Total de registros: {len(datos)}"
                )

            else:
                st.info(
                    "Este archivo no contiene pestañas disponibles."
                )

    except Exception as error:
        st.error(
            "No se pudo conectar con Google Sheets."
        )
        st.exception(error)

def choose_athlete(key='athlete'):
    if a.empty:st.info('Primero crea un deportista en Gestionar deportistas.');st.stop()
    labels={int(r.id):f'{r["name"]} · {r["club"]}' for _,r in a.iterrows()}
    selected=st.selectbox('Deportista',list(labels),format_func=lambda x:labels[x],key=key)
    return selected,a[a.id==selected].iloc[0]

if page=='Gestionar deportistas':
    st.subheader('Crear perfil')
    with st.form('new_athlete'):
        name=st.text_input('Nombre *');club=st.text_input('Club',value='Independiente');sport=st.text_input('Deporte / disciplina');objective=st.text_area('Objetivo principal')
        if st.form_submit_button('Guardar deportista'):
            try:db.add_athlete(name,club,sport,objective);st.success('Perfil guardado');st.rerun()
            except Exception as e:st.error(str(e))
    st.dataframe(a,hide_index=True,use_container_width=True)

elif page=='Importar Excel':
    st.subheader('Importación de formatos existentes')
    st.info('Selecciona el deportista correspondiente a cada archivo. Para varios atletas, importa cada archivo individualmente; no se infiere la identidad por la portada.')
    aid,person=choose_athlete()
    uploaded=st.file_uploader('Archivo Excel del deportista',type=['xlsx'])
    if uploaded:
        try:
            rows,warnings=extract(uploaded.getvalue(),aid)
            st.write(f'Mediciones detectadas: **{len(rows)}**')
            if rows:st.dataframe(pd.DataFrame(rows)[['date','kind','protocol','load_kg','value','unit']].head(30),hide_index=True)
            for warning in warnings:st.warning(warning)
            st.caption('Se omiten filas sin fecha o medición válida. Reimportar el mismo archivo omite las mediciones ya importadas; los archivos modificados deben revisarse antes de confirmar.')
            if st.button('Confirmar importación',disabled=not rows):
                saved,errors=save_rows(rows);st.success(f'{saved} mediciones importadas.')
                if errors:st.error('Algunas filas no se importaron: '+'; '.join(errors[:5]))
        except Exception as e:st.error(f'No fue posible leer el archivo: {e}')

elif page=='Registrar evaluación':
    aid,person=choose_athlete()
    with st.form('manual'):
        c1,c2,c3=st.columns(3)
        with c1:d=st.date_input('Fecha',datetime.date.today());kind=st.selectbox('Tipo',db.KINDS)
        with c2:protocol=st.text_input('Protocolo / ejercicio',placeholder='CMJ, SJ, Sentadilla, Press banca...');value=st.number_input('Resultado',min_value=0.0,step=0.01)
        with c3:unit=st.selectbox('Unidad',['cm','m/s','kg','N','s','%','puntos']);load=st.number_input('Carga externa (kg)',min_value=0.0,step=1.0)
        flight=st.number_input('Tiempo de vuelo (s), si aplica',min_value=0.0,step=0.01);contact=st.number_input('Tiempo de contacto (s), si aplica',min_value=0.0,step=0.01)
        expected=st.number_input('Velocidad esperada (m/s), si aplica',min_value=0.0,step=0.01)
        notes=st.text_area('Observaciones / intervención')
        if st.form_submit_button('Guardar evaluación'):
            if not protocol.strip():st.error('Escribe el protocolo o ejercicio.')
            else:
                try:
                    db.add_measurement(dict(athlete_id=aid,date=d.isoformat(),kind=kind,protocol=protocol.strip(),load_kg=load if kind in ['VBT','CMJ cargado','Monitoreo VBT'] else None,value=value,unit=unit,flight_s=flight or None,contact_s=contact or None,expected_velocity=expected or None,notes=notes,source='manual'))
                    st.success('Evaluación guardada')
                except Exception as e:st.error(str(e))

elif page=='Editar evaluaciones':
    aid,person=choose_athlete();df=db.measurements(aid)
    if df.empty:st.info('No hay mediciones todavía.')
    else:
        st.dataframe(df[['id','date','kind','protocol','load_kg','value','unit','notes','source']],hide_index=True,use_container_width=True)
        mid=st.selectbox('Registro a modificar (ID)',df.id.tolist(),format_func=lambda x:f'#{x} · {df.loc[df.id==x,"protocol"].iloc[0]} · {df.loc[df.id==x,"date"].iloc[0]}')
        r=df[df.id==mid].iloc[0]
        with st.form('edit'):
            date=st.date_input('Fecha',pd.to_datetime(r.date).date());protocol=st.text_input('Protocolo',value=r.protocol)
            value=st.number_input('Valor',value=float(r.value));unit=st.text_input('Unidad',value=r.unit)
            load=st.number_input('Carga (kg); 0 equivale a sin carga',value=float(r.load_kg) if pd.notna(r.load_kg) else 0.0)
            notes=st.text_area('Notas',value=r.notes or '')
            if st.form_submit_button('Guardar cambios'):
                db.update_measurement(mid,dict(date=date.isoformat(),protocol=protocol,value=value,unit=unit,load_kg=load if load else None,notes=notes));st.success('Registro actualizado');st.rerun()
        confirm=st.checkbox('Confirmo que deseo eliminar este registro')
        if st.button('Eliminar registro',disabled=not confirm):db.delete_measurement(mid);st.rerun()

elif page=='Panel del deportista':
    aid,person=choose_athlete();df=db.measurements(aid)
    st.caption(f'{person["sport"] or "Disciplina sin especificar"} | {person["club"]}')
    if df.empty:st.info('Importa o registra evaluaciones para comenzar.');st.stop()
    s=summary(df);c1,c2,c3=st.columns(3)
    c1.metric('Evaluaciones registradas',len(df));c2.metric('Protocolos',df.protocol.nunique());c3.metric('Última evaluación',df.date.max())
    st.subheader('Indicadores clave');st.dataframe(s,hide_index=True,use_container_width=True)
    kind=st.selectbox('Familia de pruebas',sorted(df.kind.unique()));subset=df[df.kind==kind]
    protocol=st.selectbox('Protocolo',sorted(subset.protocol.unique()));sub=subset[subset.protocol==protocol].copy()
    if kind in ['VBT','CMJ cargado'] and sub.load_kg.notna().any():
        fig=px.scatter(sub,x='load_kg',y='value',color='date',hover_data=['notes'],title=f'{protocol}: relación carga-resultado',labels={'load_kg':'Carga (kg)','value':f'Resultado ({sub.unit.iloc[0]})'})
        st.plotly_chart(fig,use_container_width=True)
        latest=sub[sub.date==sub.date.max()];fit=regression(latest.load_kg,latest.value)
        if fit:
            st.write(f"**Regresión última sesión:** n={fit['n']}, pendiente={fit['slope']:.4f}, R²={fit['r2']:.3f}")
            if kind=='VBT' and fit['slope']<0:
                st.caption(f"Intersección teórica con velocidad cero: {fit['x_intercept']:.1f} kg. No equivale necesariamente a una 1RM validada; requiere protocolo y velocidad mínima individual.")
            if kind=='CMJ cargado':st.caption('La extrapolación carga-altura es descriptiva; no representa directamente una capacidad máxima de fuerza.')
    else:
        fig=px.line(sub,x='date',y='value',markers=True,title=f'Evolución de {protocol}',labels={'date':'Fecha','value':f'Resultado ({sub.unit.iloc[0]})'})
        st.plotly_chart(fig,use_container_width=True)
    if kind=='Salto' and sub.contact_s.notna().any():
        valid=sub[(sub.contact_s>0)&sub.flight_s.notna()].copy()
        if not valid.empty:
            valid['RSI vuelo/contacto']=valid.flight_s/valid.contact_s
            st.caption('RSI vuelo/contacto: cociente temporal del formato original; no confundir con RSI clásico (altura/tiempo de contacto).')
            st.dataframe(valid[['date','protocol','RSI vuelo/contacto']],hide_index=True)
    if kind=='Monitoreo VBT':
        valid=sub[(sub.expected_velocity>0)&sub.value.notna()].copy()
        if not valid.empty:
            valid['Diferencia %']=100*(valid.value-valid.expected_velocity)/valid.expected_velocity
            st.dataframe(valid[['date','load_kg','value','expected_velocity','Diferencia %']],hide_index=True)
    st.subheader('Interpretación');st.write(interpretation(df))
    st.download_button('📄 Descargar informe PDF',data=create_pdf(person['name'],person['club'],df),file_name=f'informe_deportista_{aid}.pdf',mime='application/pdf')

elif page=='Comparar deportistas':
    df=db.measurements()
    if df.empty:st.info('Registra datos para comparar.');st.stop()
    clubs=st.multiselect('Clubes',sorted(df.club.unique()),default=sorted(df.club.unique()))
    df=df[df.club.isin(clubs)]
    if df.empty:st.stop()
    kind=st.selectbox('Tipo de prueba',sorted(df.kind.unique()));df=df[df.kind==kind]
    protocol=st.selectbox('Protocolo',sorted(df.protocol.unique()));df=df[df.protocol==protocol]
    if df.load_kg.notna().any():
        loads=sorted(df.load_kg.dropna().unique());load=st.selectbox('Carga comparable (kg)',loads);df=df[df.load_kg==load]
    latest=df.sort_values(['date','id']).groupby('athlete_id').tail(1)
    if latest.empty:st.info('Sin mediciones comparables.');st.stop()
    fig=px.bar(latest,x='name',y='value',color='club',barmode='group',title=f'Última medición de {protocol}',labels={'name':'Deportista','value':f'Resultado ({latest.unit.iloc[0]})'})
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(latest[['name','club','date','protocol','load_kg','value','unit']],hide_index=True,use_container_width=True)
    st.caption('La comparación requiere estandarizar cargas, instrumentos, técnica, fechas y condiciones; diferencias no implican superioridad global.')
