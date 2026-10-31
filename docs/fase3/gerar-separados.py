"""Export individual PDFs using the same verified dossier layout."""
import os
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parent
documents=['ARQUITETURA.md','SEQUENCIAS.md','MODELO-DE-DADOS.md','rfc/001-cloud-gerenciada.md','rfc/002-postgresql.md','rfc/003-autenticacao.md','adr/001-comunicacao-e-fronteiras.md','adr/002-hpa.md','adr/003-observabilidade-no-lab.md','VALIDACAO.md','ROTEIRO-VIDEO.md','ENTREGA.md']
for document in documents:
    subprocess.run([sys.executable,str(root/'gerar-dossie.py')],env={**os.environ,'FIAP_DOCUMENT':document},check=True)
