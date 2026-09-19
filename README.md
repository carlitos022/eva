# EVA - Artificial Face

EVA es un experimento de agente artificial local con rostro animado,
conversacion, memoria persistente y estado cognitivo almacenado en MySQL.

## Version actual: v0.3.0

### Cerebro local
- Qwen3 1.7B mediante Ollama
- Flask/Python
- MySQL remoto eva_ai
- contexto reciente + memoria de largo plazo
- seleccion automatica de recuerdos relevantes
- respuesta JSON estructurada

### Memoria e identidad
- conversaciones completas
- memorias autobiograficas seleccionadas
- identidad persistente de EVA
- identidad persistente del usuario
- migracion automatica de nombre/preferencia desde conversaciones antiguas
- recuperacion de recuerdos por relevancia + importancia
- contador de accesos a memorias

### Estado interno persistente
- emocion
- intensidad
- confianza
- energia
- curiosidad
- restauracion del ultimo estado al reiniciar EVA

### Relaciones
- afinidad
- confianza
- familiaridad
- notas persistentes de relacion

### Objetivos
- objetivos activos
- prioridad
- progreso
- descripcion persistente

### Pensamientos internos
EVA puede generar una nota interna breve de estado o conclusion.
No se guarda razonamiento paso a paso ni se envia esta nota al navegador.

### Decisiones
En v0.3.0 EVA toma decisiones internas durante cada interaccion:
- recordar
- hacer seguimiento
- crear un objetivo
- reflexionar
- no realizar ninguna accion

Estas decisiones se registran en MySQL. Todavia no ejecuta acciones externas
ni funciona autonomamente en segundo plano.

### Voz
- salida de voz mediante Speech Synthesis del navegador
- seleccion automatica de una voz en espanol disponible en Windows/Chrome
- boton para activar o silenciar voz
- movimiento de boca mientras la voz esta reproduciendose

### Rostro v0.2.1
El rostro visual se mantiene en la rama actual:
- seguimiento ocular
- parpadeo
- expresiones
- cejas
- boca con visemas
- gestos de escuchando/pensando/hablando

## Inicio rapido despues de actualizar

```powershell
cd C:\Users\USUARIO\Desktop\eva
git pull
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tools\test_connections.py
python app.py
```

Abre:

http://127.0.0.1:5000

La primera ejecucion de v0.3.0 crea o migra automaticamente las tablas
necesarias. No hace falta importar schema.sql manualmente.

## Ver el estado cognitivo

Con EVA detenida o ejecutandose en otra consola:

```powershell
python tools\inspect_eva.py
```

Tambien existe:

http://127.0.0.1:5000/api/cognition

Ese endpoint muestra identidad, relacion, objetivos, emocion y estadisticas,
pero no expone notas internas privadas.

## Tablas v0.3.0

```text
eva_ai
|
+-- conversations
+-- memories
+-- identity_profile
+-- relationships
+-- emotional_state
+-- goals
+-- internal_events
+-- decisions
```

## Prueba recomendada de memoria

Primero dile a EVA hechos estables, por ejemplo:

```text
Recuerda que mi bebida favorita es el cafe.
Quiero que me llames Carlitos.
Mi proyecto principal se llama EVA.
```

Luego conversa bastante o reinicia EVA y pregunta:

```text
Como prefiero que me llames?
Cual es mi bebida favorita?
Que proyecto estamos desarrollando?
```

Revisa despues:

```powershell
python tools\inspect_eva.py
```

## Proximos pasos

- autonomia en segundo plano con ciclos controlados
- gestion de objetivos y progreso
- voz local neural de mayor calidad
- entrada por microfono
- sincronizacion labial basada en audio real
- memoria semantica mediante embeddings locales
- futura evolucion a rostro 3D
