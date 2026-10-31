"""Build the concise Portal submission PDF from editable, non-secret JSON metadata."""
import html
import json
from pathlib import Path
from urllib.parse import urlparse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/'docs/fase3/entrega-portal.json').read_text())
OUT=ROOT/'output/pdf/fiap-fase3-entrega-portal.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
for name,file in [('Portal','DejaVuSans.ttf'),('PortalBold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('Portal',normal='Portal',bold='PortalBold',italic='Portal',boldItalic='PortalBold')
NAVY=colors.HexColor('#17324d');BLUE=colors.HexColor('#195e94');MUTED=colors.HexColor('#53697a')
style=ParagraphStyle('body',fontName='Portal',fontSize=9.5,leading=14,spaceAfter=6,textColor=NAVY)
small=ParagraphStyle('small',parent=style,fontSize=8.5,leading=12)
heading=ParagraphStyle('heading',parent=style,fontName='PortalBold',fontSize=13,leading=18,spaceBefore=12,spaceAfter=8,keepWithNext=True)
title=ParagraphStyle('title',parent=heading,fontSize=24,leading=30,spaceBefore=0,spaceAfter=8)
def para(text,s=style):return Paragraph(text,s)
def link(label,url):
    assert urlparse(url).scheme=='https'
    return '<a href="'+html.escape(url,quote=True)+'" color="#195e94">'+html.escape(label)+'</a>'
def block(text):
    table=Table([[para(text,small)]],colWidths=[507]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#edf3f8')),('BOX',(0,0),(-1,-1),.6,colors.HexColor('#bccedc')),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));return table
video=DATA['video_url'];seconds=DATA['video_duracao_segundos']
if video:
    assert urlparse(video).hostname in ['youtube.com','www.youtube.com','youtu.be','vimeo.com','www.vimeo.com']
    assert isinstance(seconds,int) and 0<seconds<=900
ready=bool(video and seconds and not DATA['pendencias_tecnicas'] and all(r['avaliador_confirmado'] for r in DATA['repositorios']))
status='Versão para submissão' if ready else 'VERSÃO PRELIMINAR - NÃO ENVIAR AINDA'
notes=[]
if not video: notes.append('O vídeo ainda não foi incluído.')
if DATA['pendencias_tecnicas']: notes.append('Há pendências técnicas na matriz de validação.')
if not all(r['avaliador_confirmado'] for r in DATA['repositorios']): notes.append('O acesso do avaliador precisa ser confirmado.')
notice=' '.join(notes)+' Este arquivo prepara a entrega e não declara conformidade integral.'

def furniture(c,d):
    c.setFillColor(NAVY);c.rect(0,A4[1]-31,A4[0],31,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setFont('PortalBold',9);c.drawString(44,A4[1]-21,'FIAP / TECH CHALLENGE / FASE 3')
    c.setFillColor(MUTED);c.setFont('Portal',8);c.drawString(44,23,'Oficina - documento de entrega | Revisão '+DATA['revisao'])
    c.drawRightString(A4[0]-44,23,str(d.page))

story=[para('Documento de entrega',title),para('Sistema de oficina mecânica - Tech Challenge / Fase 3'),para('Links para avaliação no Portal do Aluno',small),Spacer(1,10),block('<b>'+status+'</b><br/>'+notice if not ready else '<b>'+status+'</b>'),para('1. Repositórios do projeto',heading)]
for i,r in enumerate(DATA['repositorios'],1):
    url=r['url'];story.append(KeepTogether([para(f'<b>{i}. {html.escape(r["nome"])}</b> - {html.escape(r["proposito"])}'),para(link(url,url),small),para('Código do ambiente demonstrado: '+link('branch homolog',url+'/tree/homolog')+' | '+link('Pipelines',url+'/actions'),small),Spacer(1,7)]))
story.extend([para('2. Vídeo de demonstração',heading)])
if video:
    story.extend([para(link(video,video)),para(f'Duração conferida nos metadados do YouTube: {seconds//60}min{seconds%60:02}s. Link acessível sem login na conferência de 31/10/2026.',small)])
else:
    story.append(block('<b>Link do vídeo: PENDENTE DE GRAVAÇÃO</b><br/>Publicar no YouTube ou Vimeo, público ou não listado, com duração máxima de 15 minutos. Incluir aqui a URL e a duração antes do envio.'))
story.append(para('O vídeo deve demonstrar autenticação por CPF, pipeline e deploy automático, consumo de APIs protegidas, dashboard ao vivo, logs e traces.',small))
story.extend([PageBreak(),para('3. Documentação arquitetural',heading),para('Documentação publicada no repositório de infraestrutura Kubernetes. Os links abaixo são clicáveis; os PDFs individuais complementam o dossiê.',small)])
rows=[[para('<b>Conteúdo</b>',small),para('<b>Documento / acesso</b>',small)]]
for label,links in DATA['documentacao']:
    rows.append([para(html.escape(label),small),para(' | '.join(link(title,url) for title,url in links),small)])
table=Table(rows,colWidths=[168,339],repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce8f1')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7fa')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(table)
story.extend([para('4. Acesso do avaliador',heading),para('Usuário GitHub: <b>soat-architecture</b>. Sua inclusão como colaborador foi reconfirmada via API do GitHub em '+DATA['avaliador_verificado_em']+'.',small)])
for r in DATA['repositorios']:
    story.append(para(('Confirmado' if r['avaliador_confirmado'] else 'Pendente')+' - '+html.escape(r['nome']),small))
story.extend([para('Acessos complementares',heading),para(' | '.join(link(label,url) for label,url in DATA['acessos']),small),para('Os endpoints de homologação dependem do Learner Lab ativo. O documento não contém senhas, tokens ou credenciais. O avaliador acessa código e documentação pelos repositórios.',small),block('<b>Antes de enviar:</b> '+('incluir o vídeo (até 15 minutos), ' if not video else 'conferir o conteúdo e o acesso ao vídeo, ')+ 'fechar as pendências da '+link('matriz de validação',DATA['matriz_url'])+', conferir os links e reconfirmar o acesso do avaliador. Não é necessário anexar todos os arquivos separadamente ao Portal: o enunciado pede um PDF único com esses links.')])
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=52,bottomMargin=43,title='FIAP - Oficina - Entrega no Portal - Fase 3',author='Projeto Oficina / FIAP')
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
print(OUT)
