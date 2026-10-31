"""Build the review dossier from Markdown and exported diagrams (ReportLab/Pillow)."""
from pathlib import Path
import re, html, posixpath, os, json
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, NextPageTemplate, LongTable, TableStyle, Image
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

root=Path(__file__).resolve().parents[2]
source=root/'docs/fase3'
delivery=json.loads((source/'entrega-portal.json').read_text())
video_url=delivery.get('video_url')
video_seconds=delivery.get('video_duracao_segundos')
video_duration=(f'{video_seconds//60}min{video_seconds%60:02}s' if video_seconds else 'duração a conferir')
video_summary=('Vídeo incluído: <a color="#1d5c8e" href="'+html.escape(video_url,quote=True)+'">YouTube</a> ('+video_duration+'). Conteúdo e pendências técnicas ainda requerem revisão.' if video_url else 'O vídeo será gravado pelo usuário após finalizar as pendências.')
individual=os.environ.get('FIAP_DOCUMENT')
output=root/'output/pdf'/('separados/'+individual.replace('/', '-').replace('.md','.pdf') if individual else 'fiap-fase3-dossie-tecnico.pdf')
output.parent.mkdir(parents=True,exist_ok=True)
fonts=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Body','DejaVuSans.ttf'),('Body-Bold','DejaVuSans-Bold.ttf'),('Body-Oblique','DejaVuSans-Oblique.ttf'),('Body-BoldOblique','DejaVuSans-BoldOblique.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Oblique',boldItalic='Body-BoldOblique')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=9.1,leading=13.3,spaceAfter=6,textColor=colors.HexColor('#20364b'),splitLongWords=True))
styles.add(ParagraphStyle(name='H1Custom',parent=styles['Text'],fontName='Body-Bold',fontSize=21,leading=27,spaceAfter=15,keepWithNext=True))
styles.add(ParagraphStyle(name='H2Custom',parent=styles['Text'],fontName='Body-Bold',fontSize=12,leading=17,spaceBefore=13,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='CellCustom',parent=styles['Text'],fontSize=8,leading=11.2,spaceAfter=0))
styles.add(ParagraphStyle(name='NoteCustom',parent=styles['Text'],fontSize=8,leading=11,textColor=colors.HexColor('#546b80')))
styles.add(ParagraphStyle(name='TitleCustom',parent=styles['H1Custom'],fontSize=30,leading=38))
urlbase='https://github.com/15SOAT-JVGG/oficina-infra-k8s/blob/main/docs/fase3/'
def inline(text,parent):
    text=html.escape(text)
    def link(m):
        label,target=m.groups()
        if not target.startswith(('https://','http://')):
            target=urlbase+posixpath.normpath(str(parent.relative_to(source)/target))
        return '<a color="#1d5c8e" href="'+target+'">'+label+'</a>'
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,text)
    text=re.sub(r'`([^`]+)`',r'<font name="Mono">\1</font>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
    return text

def furniture(c,doc):
    w,h=c._pagesize
    c.setFillColor(colors.HexColor('#17324d'));c.rect(0,h-28,w,28,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setFont('Body-Bold',9);c.drawString(44,h-19,'FIAP / OFICINA / FASE 3')
    c.setFillColor(colors.HexColor('#62788b'));c.setFont('Body',7.5)
    c.drawString(44,22,'Dossiê técnico - revisão de homologação - consultar matriz de validação')
    c.drawRightString(w-44,22,str(doc.page))

doc=BaseDocTemplate(str(output),pagesize=A4,title='Oficina - Dossiê técnico da Fase 3',author='Projeto Oficina / FIAP',leftMargin=44,rightMargin=44,topMargin=48,bottomMargin=40)
pw,ph=A4;lw,lh=landscape(A3)
doc.addPageTemplates([
 PageTemplate(id='Portrait',frames=[Frame(44,42,pw-88,ph-94,id='portrait',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture,pagesize=A4),
 PageTemplate(id='Landscape',frames=[Frame(35,42,lw-70,lh-94,id='landscape',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture,pagesize=landscape(A3))])
story=[Spacer(1,68),Paragraph('Oficina<br/>Dossiê técnico da Fase 3',styles['TitleCustom']),Spacer(1,20),Paragraph('Arquitetura, componentes, sequências, modelo relacional, RFCs, ADRs e validação do ambiente de homologação.',styles['Text']),Spacer(1,20),Paragraph('<b>Revisão de 31/10/2026 (BRT)</b>',styles['Text']),Paragraph('Este documento registra a solução observada e suas pendências. Não declara conformidade integral. O PDF de links para o Portal está em arquivo próprio; a matriz registra a revisão técnica ainda necessária.',styles['Text']),Spacer(1,25),Paragraph(video_summary+' A massa contém somente CPF e IDs gerados para demonstração. Nenhuma senha, token ou credencial é incluída.',styles['Text']),PageBreak()]
order=['COMECE-AQUI.md','MASSA-PRONTA.md','README.md','ARQUITETURA.md','SEQUENCIAS.md','MODELO-DE-DADOS.md','rfc/001-cloud-gerenciada.md','rfc/002-postgresql.md','rfc/003-autenticacao.md','adr/001-comunicacao-e-fronteiras.md','adr/002-hpa.md','adr/003-observabilidade-no-lab.md','VALIDACAO.md','ROTEIRO-VIDEO.md','ENTREGA.md']
if individual:
    if individual not in order or individual == 'README.md': raise ValueError('Documento desconhecido')
    order=[individual]
    story=[]
for file_index,name in enumerate(order):
    path=source/name;lines=path.read_text().splitlines();i=0;figures=[]
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        image=re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',line)
        if image:figures.append((image.group(1),path.parent/image.group(2)));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            n=max(len(r) for r in rows);ratios={2:[.28,.72],3:[.27,.18,.55],4:[.2,.2,.35,.25]}.get(n,[1/n]*n)
            if rows[0][0]=='Tempo': ratios=[.17,.43,.40]
            if rows[0][0]=='Repositório / pipeline': ratios=[.26,.39,.35]
            data=[[Paragraph(inline(c,path.parent),styles['CellCustom']) for c in r+['']*(n-len(r))] for r in rows]
            table=LongTable(data,colWidths=[(pw-88)*v for v in ratios],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0ebf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fb')]),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8ea8bd')),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,9)]);continue
        if line.startswith('# '):story.append(Paragraph(inline(line[2:],path.parent),styles['H1Custom']));i+=1;continue
        if line.startswith('### '):story.append(Paragraph(inline(line[4:],path.parent),styles['H2Custom']));i+=1;continue
        if line.startswith('## '):story.append(Paragraph(inline(line[3:],path.parent),styles['H2Custom']));i+=1;continue
        if line.startswith('- ') or re.match(r'^\d+\. ',line):
            story.append(Paragraph(inline(line,path.parent),styles['Text']));i+=1;continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','|','- ','![')) and not re.match(r'^\d+\. ',lines[i].strip()):para.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(' '.join(para),path.parent),styles['Text']))
    for figure_index,(title,imagepath) in enumerate(figures):
        if figure_index==0: story.extend([NextPageTemplate('Landscape'),PageBreak()])
        else: story.append(PageBreak())
        story.append(Paragraph(title,styles['H2Custom']))
        with PILImage.open(imagepath) as im:iw,ih=im.size
        scale=min((lw-86)/iw,(lh-135)/ih)
        story.append(Image(str(imagepath),width=iw*scale,height=ih*scale))
        story.append(Paragraph('Fonte editável e versão vetorial no diretório docs/fase3/diagramas. Diagrama de homologação; limites e caminhos alternativos no texto.',styles['NoteCustom']))
    if figures: story.extend([NextPageTemplate('Portrait'),PageBreak()])
    if file_index<len(order)-1 and not figures:story.append(PageBreak())
doc.build(story)
print(output)
