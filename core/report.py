from io import BytesIO
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from core.analysis import summary,interpretation

def create_pdf(name,club,df):
    output=BytesIO();doc=SimpleDocTemplate(output,pagesize=(595,842),leftMargin=42,rightMargin=42)
    styles=getSampleStyleSheet();story=[Paragraph('Informe de rendimiento deportivo',styles['Title']),Spacer(1,12),Paragraph(f'Deportista: {name} | Club: {club}',styles['Normal']),Spacer(1,16)]
    s=summary(df)
    if not s.empty:
        rows=[['Prueba / protocolo','Último','Unidad','Cambio %']]
        for _,r in s.iterrows():
            change='—' if r['Cambio %']!=r['Cambio %'] else f"{r['Cambio %']:+.1f}%"
            rows.append([str(r['Protocolo'])[:30],f"{r['Último']:.2f}",r['Unidad'],change])
        t=Table(rows,colWidths=[235,75,65,80],repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#14283e')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eef3f7')]),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9)]))
        story.extend([t,Spacer(1,18)])
    story.append(Paragraph('Interpretación descriptiva',styles['Heading2']))
    story.append(Paragraph(interpretation(df),styles['BodyText']))
    story.extend([Spacer(1,16),Paragraph('Nota: Las estimaciones y tendencias no sustituyen el juicio profesional ni equivalen a diagnósticos de fatiga o rendimiento.',styles['Italic'])])
    doc.build(story);return output.getvalue()
