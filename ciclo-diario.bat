@echo off
REM ---------------------------------------------------------------------
REM  ULTRA CHAMBA - ciclo diario
REM
REM  Lanza `app/dia.py`: recolecta, limpia, sigue el correo, prepara la cola
REM  del dia y regenera los derivados. Deja todo listo para que el usuario
REM  solo tenga que aprobar en el panel.
REM
REM  Existe como .bat y no como una linea directa en el Programador de
REM  tareas porque la ruta lleva un espacio ("ULTRA CHAMBA") y el
REM  entrecomillado de schtasks se rompe con ella. Aqui no hay nada que
REM  escapar.
REM
REM  Se puede ejecutar a mano con doble clic.
REM ---------------------------------------------------------------------

cd /d "%~dp0"

REM Se prefiere el Python del entorno virtual del proyecto: es el que tiene las
REM dependencias instaladas (ver requirements.txt). Si no existe, se cae al del
REM PATH, que puede no tenerlas y hacer fallar el primer import.
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" -X utf8 "%~dp0app\dia.py" %*

REM Nunca devuelve error al Programador: si un paso falla, queda anotado en
REM datos/dia.log y el resto del ciclo ya se ejecuto igual.
exit /b 0
