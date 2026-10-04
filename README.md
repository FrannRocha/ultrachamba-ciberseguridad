# ULTRA CHAMBA — ciberseguridad

Buscador, clasificador y panel de **vacantes de ciberseguridad e IA de nivel
inicial** (prácticas, becario, junior) en el mercado mexicano y en remoto.
Recolecta de fuentes públicas, descarta lo que no encaja **explicando por qué**,
comprueba que la vacante siga viva, y deja el trabajo del día en una cola corta
con el correo ya redactado para que tú solo revises y envíes.

> **Antes de nada: edita `app/perfil.py`.** Viene con una plantilla de valores
> `EJEMPLO — …` claramente ficticios. De ese archivo salen el scoring, los
> correos y el rótulo del panel: si no lo rellenas, el sistema funciona pero
> puntúa contra un perfil vacío.

---

## 1. Propósito y público

Está pensado para **alguien que estudia o empieza en ciberseguridad** y necesita
convertir "hay miles de vacantes" en "hoy toco estas tres puertas". El problema
que ataca no es encontrar anuncios: es que una lista larga no produce
candidaturas.

- **Público:** estudiantes y perfiles de nivel inicial en seguridad de la
  información, GRC, Blue Team/SOC y seguridad de IA.
- **Mercado por defecto:** área metropolitana de Monterrey (México) + remoto
  abierto a México. Es un valor por defecto de mercado, no una limitación del
  código: se cambia en `app/perfil.py`.
- **No es** un scraper masivo ni un autopostulador. No envía nada sin tu gesto.

## 2. Funcionalidades disponibles

**Recolección y clasificación**
- Colectores de ATS públicos (Greenhouse, Lever, Ashby y similares), bolsas
  mexicanas, LinkedIn público y, opcionalmente, Indeed.
- Clasificador de dominio (`app/dominio.py`): separa ciberseguridad real de la
  auditoría contable o la seguridad física, que usan las mismas palabras.
- Scoring contra tu perfil (`app/analisis.py`) con geografía (`app/geo.py`) y
  años de experiencia exigidos (`app/experiencia.py`). Cada vacante llega con
  los motivos escritos.
- Detector de **vacantes fantasma** (`app/fantasma.py`): anuncios que llevan
  demasiado tiempo abiertos o se republican sin contratar.

**Verificación**
- Tres capas (`app/verificador.py`, `app/verificar_pendientes.py`,
  `app/verificador_chrome.py`) para saber si la vacante sigue viva. La tercera
  genera JavaScript que **tú** pegas en una pestaña ya abierta del portal: usa
  tu propia sesión, no guarda credenciales ni abre navegadores por su cuenta.

**Panel**
- Servidor local (`app/servidor.py`) que sirve `panel.html` y consulta SQLite.
  Filtros por prioridad, área, nivel, modalidad y verificación; búsqueda;
  pestañas de vacantes, formación y plan del día. Vista móvil en `/movil`.

**Trabajo del día**
- Cola corta (`app/cola.py`) con el correo redactado (`app/generador_correos.py`,
  `app/correos_frios.py`), aprobaciones (`app/aprobaciones.py`) y seguimiento de
  lo enviado (`app/seguimiento.py`, `app/tramites.py`).

**Formación**
- Cursos y becas gratuitos (`app/cursos.py`, `app/fuentes_cursos.py`,
  `app/formacion.py`) puntuados contra lo que piden las vacantes de tu base, no
  por prestigio de marca.

**Integraciones opcionales (desactivadas por defecto)**
- Gmail (`app/correo_gmail.py`): deja borradores; leer y enviar exigen permisos
  y gestos tuyos aparte. Ver §5.
- Drive/NotebookLM (`app/sincronizar_drive.py`, `app/exportar_corpus.py`).
- Bóveda de Obsidian (`app/generar_obsidian*.py`) y dashboard estático
  (`app/generar_dashboard.py`).

## 3. Requisitos

**Imprescindibles**

- **Python 3.12** (probado en 3.12.3).
- **Windows 10 u 11** (es donde se probó). El núcleo es Python estándar y
  *debería* funcionar en Linux y macOS, pero **no se ha probado ahí**, y allí
  te quedas sin los `.bat` y sin la apertura automática de Chrome.
- Un navegador para abrir el panel.
- Conexión a internet para recolectar (peticiones GET a fuentes públicas).

**Opcionales — el núcleo funciona sin todos ellos**

| Qué | Para qué | Si falta |
|---|---|---|
| **Google Chrome** | `app/agente_local.py` lo abre para ejecutar lo que apruebas, y el flujo de fichas de OCC usa una pestaña tuya | Busca Chrome en tres rutas típicas de Windows; si no lo encuentra, usa tu navegador por defecto |
| **Cuenta de Google propia + credenciales OAuth** | Borradores en tu Gmail, seguimiento de respuestas, copia a tu Drive | Esos módulos avisan y no hacen nada; el resto sigue igual |
| **`requirements-opcional.txt`** | Las librerías de Google que necesitan Gmail y Drive | Sin instalarlas, esos módulos fallan con `ImportError` al usarlos |
| **Clave de la API de Indeed** | Activa esa fuente (`INDEED_API_KEY`) | La fuente se desactiva sola y lo dice por el log |
| **Obsidian** | Abrir la bóveda que generan `app/generar_obsidian*.py` | Las notas se generan igual: son archivos Markdown |
| **Git** | Publicar el proyecto (sección 9) | Todo lo demás funciona sin él |

> **Nota sobre las tipografías.** `panel.html` carga Bebas Neue y Mulish desde
> `fonts.googleapis.com` / `fonts.gstatic.com`. Sin internet, el panel se ve con
> las tipografías de reserva del sistema: cambia el aspecto, no el
> funcionamiento.

## 4. Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

**Solo si vas a usar Gmail o Google Drive**, instala además las librerías de
Google. No están en `requirements.txt` a propósito: el núcleo —recolectar,
clasificar, verificar y el panel— funciona entero sin ellas.

```bash
pip install -r requirements-opcional.txt
```

No hace falta crear `app/datos/`: el código la crea sola al arrancar.

## 5. Configuración

**a) Tu perfil — obligatorio.** Edita `app/perfil.py`:
- `CANDIDATO`: nombre, correo, teléfono, enlaces, ciudad.
- `POSTULACION`: las respuestas que piden los formularios de las bolsas. Lo que
  dejes en `None` **no se inventa**: el sistema para y te lo pregunta.
- `LOGROS`, `CERTIFICACIONES`, `COMPETENCIAS`: solo lo que puedas sostener en
  una entrevista.
- El resto del archivo (`HABILIDADES`, `AREA_*`, `NIVEL_*`, geografía) **no es
  personal**: es el vocabulario del clasificador. Tócalo solo si quieres afinar
  el criterio.

**b) Variables de entorno — opcionales.** Ver `.env.example`. Hoy solo hay una,
`INDEED_API_KEY`, y el código **no carga `.env` automáticamente**: expórtala en
tu terminal si la vas a usar. Sin ella, la fuente de Indeed se desactiva sola y
lo dice por el log.

**c) Google — opcional.** Hacen falta **dos cosas**, y sin las dos no funciona:

1. Las librerías: `pip install -r requirements-opcional.txt`. Si te saltas este
   paso, los módulos de Gmail y Drive fallan con `ImportError` al usarlos.
2. Tus credenciales OAuth de escritorio, descargadas de Google Cloud Console y
   guardadas en `app/datos/credenciales_drive.json` (está en `.gitignore`).

Sin credenciales, los módulos de correo y Drive avisan y no hacen nada. El
resto del sistema funciona igual.

**d) Envío de correo — tres llaves, las tres tuyas.** Para que el sistema pueda
*enviar* y no solo dejar borradores hacen falta a la vez: (1) un token de Gmail
con permiso de envío, (2) el interruptor `app/datos/permitir_envio.json`, y
(3) una candidatura que tú hayas aprobado en el panel. Si falta una, no sale
nada. Cada envío queda registrado en `app/datos/envios.log`.

## 6. Ejecución local

```bash
# El panel (lo más habitual)
python app/servidor.py                 # http://127.0.0.1:8800
python app/servidor.py --puerto 8811   # otro puerto: el 8800 puede estar ocupado
                                       # por otra copia del proyecto
python app/servidor.py --host 0.0.0.0  # en la red: exige token, lo imprime

# El ciclo completo del día: recolectar, analizar, seguir y preparar la cola
python app/dia.py

# Piezas sueltas
python app/pipeline.py        # recolección + análisis
python app/excavadora.py      # recolección amplia por oleadas
python app/generar_todo.py    # regenera dashboard y bóveda
python app/salud.py           # comprobaciones de integridad de los datos
```

En Windows hay dos atajos: `ciclo-diario.bat` (el ciclo del día) y
`agente-en-casa.bat` (panel en red + agente que ejecuta lo aprobado). Los dos
prefieren el Python del `.venv` del proyecto y, si no existe, caen al del PATH.

> **`agente-en-casa.bat` saca el panel a la red.** Úsalo solo en una **red de
> confianza** o detrás de una **VPN privada** — `app/servidor.py` sugiere
> Tailscale, para que solo lleguen tus dispositivos. **Nunca en una wifi
> pública.** El token es obligatorio al salir a la red y el servidor lo imprime
> al arrancar, pero es la cerradura mínima, no cifrado.

### Este proyecto no programa nada por su cuenta

No registra tareas en el Programador de tareas de Windows, no se añade al inicio
de sesión y no deja nada corriendo en segundo plano: los `.bat` se ejecutan sólo
cuando tú los lanzas. Si quieres que el ciclo diario corra solo, regístralo tú:

```bat
schtasks /create /tn "ULTRA CHAMBA - ciclo diario" ^
  /tr "\"C:\ruta\a\tu\copia\ciclo-diario.bat\"" ^
  /sc daily /st 07:00 /rl LIMITED
```

`/rl LIMITED` es deliberado: privilegios normales, sin UAC. Para quitarla:
`schtasks /delete /tn "ULTRA CHAMBA - ciclo diario" /f`.

Antes de programarlo, ten claro lo que implica: una tarea así **sale a internet
a recolectar y escribe en `app/datos/` sin que tú estés delante**, y si además
programas `agente-en-casa.bat` habrá un proceso ejecutando lo que hayas
aprobado. Comprueba primero a mano que el ciclo hace lo que esperas.

La primera vez la base está vacía: el panel dirá que no hay datos hasta que
corras una recolección.

## 7. Pruebas

Los `app/test_*.py` **son scripts con `main()`, no tests de pytest**: `pytest`
los recoge como 0 tests y sale con código 5. Se ejecutan directamente:

```bash
python app/test_modulos.py     # clasificador de dominio, geo y experiencia
python app/test_analisis.py    # scoring de extremo a extremo
python app/test_fantasma.py    # detector de vacantes fantasma (crea la base)
python app/test_formacion.py   # elegibilidad de cursos (crea la base)
python app/test_indeed.py      # sin INDEED_API_KEY dice «NO EJECUTADO» y sale con 0;
                               # CON clave hace peticiones REALES a Indeed
```

Comprobación estática sin instalar nada extra:

```bash
python -m compileall -q app
```

## 8. Fuentes de datos y limitaciones

**Fuentes.** ATS públicos de empresas, bolsas de empleo mexicanas, LinkedIn
público, portales de cursos y becas. Todo por peticiones GET a páginas
públicas, con caché en disco para no repetir consultas.

**Limitaciones conocidas, medidas y no disimuladas:**
- **OCC responde 403** a cualquier petición directa a la ficha de una vacante.
  Por eso el detalle se lee con el flujo de Chrome (§2), que exige un gesto tuyo.
- **Indeed** requiere `INDEED_API_KEY`. Sin ella esa fuente aporta cero, y lo
  dice; no finge recolectar.
- **Ubicación inventada:** algunos parsers rellenan `"Nuevo Leon, Mexico"` como
  ubicación por defecto cuando el anuncio no la trae. Eso etiqueta vacantes en
  Nuevo León sin que lo estén; `app/salud.py` lo mide como `ubicacion-inventada`.
  Se conserva el comportamiento del proyecto original — tenlo en cuenta al leer
  el filtro "En Monterrey".
- **Descripciones recortadas:** OCC y Computrabajo entran con el texto de la
  tarjeta de resultados, no completo. Los conteos de habilidades se apoyan sobre
  todo en LinkedIn y en bolsas oficiales.
- **Contactos y empresas de ejemplo:** `app/datos_contactos.py` y
  `app/datos_empresas.py` traen entradas ficticias e inertes (dominios
  `example.com`, confianza `no-verificado`, score 0). Son una plantilla, **no
  oportunidades reales**. Un correo inferido por patrón puede rebotar: el campo
  `correo_origen` lo dice y el panel lo enseña.
- **Sin datos de partida:** este repositorio no incluye base de datos, caché ni
  exportaciones. Todo se genera en tu máquina.

## 9. Privacidad

- `app/datos/` (base, respaldos, cachés, tokens, registros) está en
  `.gitignore` y **no** forma parte del repositorio.
- No se incluye ninguna credencial, token ni clave de API.
- `app/perfil.py` es una plantilla con valores `EJEMPLO — …` ficticios.
- Antes de subir cualquier cambio, revisa qué entra: `git status` y
  `git ls-files --cached`.

## 10. Publicar en GitHub

El repositorio está inicializado en `main` y con los archivos preparados, pero
**sin ningún commit**: el commit graba tu nombre y tu correo en los metadatos, y
esa decisión es tuya.

```bash
# 1. Comprueba qué se va a subir
git status
git ls-files --cached

# 2. Identifícate (una vez, si no lo tienes configurado)
git config user.name  "Tu Nombre"
git config user.email "tu-correo@example.com"

# 3. El primer commit
git commit -m "ULTRA CHAMBA — ciberseguridad: version inicial"

# 4. Crea el repositorio VACÍO en github.com y enlázalo
git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
git push -u origin main
```

**Antes del `push`:** decide si el repositorio será público o privado, y revisa
que `app/perfil.py` no lleve tus datos reales si no quieres publicarlos.

**Licencia:** MIT (archivo `LICENSE`). Puedes usar, modificar y redistribuir
el código conservando el aviso de copyright.

**Atribuciones de terceros:** `app/vendor/` incluye React y htm con sus
cabeceras de licencia originales; consérvalas.
