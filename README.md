# kiwifybot

Aplicação local para baixar vídeos e anexos de cursos aos quais sua conta da
Kiwify possui acesso legítimo.

## Segurança

- A senha não é salva em arquivo. Ela é enviada por HTTPS ao Google Identity
  Toolkit, serviço de autenticação usado pela Kiwify.
- O token de autenticação só é enviado a domínios `kiwify.com.br`.
- Downloads redirecionados para Google Storage ou outras CDNs usam uma sessão
  limpa, sem o token da Kiwify.
- O servidor Flask escuta somente em `127.0.0.1`.
- Downloads que alteram o sistema usam `POST` com proteção CSRF.

Use apenas para conteúdo que você tem autorização para baixar e observe os
termos da plataforma e do produtor do curso.

## Instalação

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Interface web

```powershell
python app.py
```

Abra `http://127.0.0.1:5000` e informe suas credenciais. Elas permanecem apenas
na memória do processo.

Também é possível fornecer `KIWIFY_EMAIL`, `KIWIFY_PASSWORD` e
`FLASK_SECRET_KEY` por variáveis de ambiente.

## Baixar todos os cursos

```powershell
python download_all.py
```

O comando solicita a senha sem exibi-la, baixa todos os vídeos e anexos para
`Cursos/`, ignora arquivos já concluídos e retoma transferências de vídeo
interrompidas.

## Testes

```powershell
python -m unittest discover -s tests -v
```
