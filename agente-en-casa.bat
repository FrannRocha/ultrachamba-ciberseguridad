@echo off
REM ---------------------------------------------------------------------
REM  ULTRA CHAMBA - el agente de casa (para aprobar desde el telefono)
REM
REM  Arranca dos cosas y las deja corriendo:
REM
REM    1. El panel escuchando EN LA RED, con su vista movil y su token.
REM       Imprime el enlace: abrelo una vez en el telefono y quedara
REM       guardado (el token se recuerda en el navegador).
REM    2. El agente local, que cada tres minutos ejecuta lo que el usuario
REM       aprobo: manda el correo o abre la pestana del portal en Chrome.
REM
REM  POR QUE HACEN FALTA LOS DOS. El panel recoge el si; el agente lo
REM  ejecuta. Si solo corre el panel, las aprobaciones se quedan en la cola
REM  (el arranque de la siguiente sesion lo avisara). Si solo corre el
REM  agente, no hay desde donde aprobar.
REM
REM  SEGURIDAD. El panel sale a la red con token obligatorio, y la
REM  recomendacion es Tailscale: asi solo llegan los dispositivos de
REM  El usuario y no cualquiera que comparta la wifi. Con Tailscale, la
REM  direccion del telefono es la 100.x.y.z de esta maquina.
REM
REM  Se cierra cerrando las dos ventanas que abre.
REM ---------------------------------------------------------------------

cd /d "%~dp0"

REM Se prefiere el Python del entorno virtual del proyecto: es el que tiene las
REM dependencias instaladas (ver requirements.txt). Si no existe, se cae al del
REM PATH, que puede no tenerlas y hacer fallar el primer import.
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM El token se puede fijar aqui para que el enlace del telefono no cambie
REM cada vez que se reinicia. Si se deja vacio, el servidor genera uno nuevo
REM en cada arranque y hay que volver a abrir el enlace en el movil.
set TOKEN=

if "%TOKEN%"=="" (
  start "ULTRA CHAMBA - panel movil" "%PY%" -X utf8 "%~dp0app\servidor.py" --host 0.0.0.0
) else (
  start "ULTRA CHAMBA - panel movil" "%PY%" -X utf8 "%~dp0app\servidor.py" --host 0.0.0.0 --token %TOKEN%
)

start "ULTRA CHAMBA - agente local" "%PY%" -X utf8 "%~dp0app\agente_local.py"

echo.
echo  Dos ventanas abiertas: el panel (mira ahi el enlace con el token) y el agente.
echo  Vista movil en esta maquina: http://127.0.0.1:8800/movil
echo.
exit /b 0
