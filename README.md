# EVA - Artificial Face

EVA es un agente artificial local experimental con rostro animado, conversacion,
memoria persistente y un nucleo cognitivo almacenado en MySQL.

## Version actual: v0.4.0 - Memory Cortex

La v0.4 toma ideas arquitectonicas de sistemas de agentes modernos como
OpenHuman, pero las implementa de forma propia y ligera en Python para EVA.
No se copia el core GPL de OpenHuman.

### Cerebro local
- Qwen3 1.7B mediante Ollama
- Flask/Python
- MySQL remoto eva_ai
- contexto reciente + memoria de largo plazo
- respuesta JSON estructurada
- Memory Cortex con fallback automatico

### Memory Cortex v0.4
- recuperacion hibrida lexical + semantica
- embeddings locales opcionales con bge-m3
- degradacion automatica a memoria lexical si bge-m3 no esta disponible
- puntuacion por semantica, coincidencia lexical, importancia, fuerza,
  actualidad, accesos y valor emocional
- refuerzo de recuerdos utilizados
- hash persistente de recuerdos
- Memory Tree compacto por ramas
- entidades persistentes
- relaciones entre entidades
- tareas preparadas para objetivos
- migracion automatica desde v0.3

### Archivist post-turn
EVA ya no depende solamente del mismo turno visible para aprender.

Despues de responder, un worker en segundo plano analiza el intercambio y puede:
- extraer varios recuerdos
- actualizar identidad estable
- detectar personas, proyectos, organizaciones, lugares y tecnologias
- crear relaciones entre entidades
- detectar objetivos duraderos
- generar embeddings de nuevos recuerdos

El Archivist nunca guarda razonamiento paso a paso.

### Event Bus
La v0.4 agrega un bus de eventos interno para desacoplar:
- mensajes del usuario
- respuestas de EVA
- consolidacion post-turn
- futuros eventos autonomos

### Heartbeat seguro
Existe un motor de heartbeat preparado para autonomia futura.

En v0.4:
- esta desactivado por defecto
- no ejecuta acciones externas
- cuando se activa solo publica ciclos NO_OP y estado
- EVA_AUTONOMY_ENABLED permanece separado

### Memoria e identidad
- conversaciones completas
- memorias autobiograficas
- identidad persistente de EVA
- identidad persistente del usuario
- preferencias y hechos
- memoria por importancia
- contador de accesos
- entidades y relaciones
- Memory Tree

### Estado interno persistente
- emocion
- intensidad
- confianza
- energia
- curiosidad
- restauracion al reiniciar EVA

### Relaciones y objetivos
- afinidad
- confianza
- familiaridad
- notas persistentes
- objetivos activos
- prioridad
- progreso
- tareas preparadas para la siguiente etapa

### Voz y rostro
Se conserva la base visual actual:
- seguimiento ocular
- parpadeo
- expresiones
- cejas
- boca con visemas
- gestos de escuchando, pensando y hablando
- Speech Synthesis del navegador

## Actualizar desde v0.3

En PowerShell:

```powershell
cd C:\Users\USUARIO\Desktop\eva
git pull
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Para activar memoria semantica recomendamos instalar una sola vez:

```powershell
ollama pull bge-m3
```

Si no instalas bge-m3, EVA NO deja de funcionar. La v0.4 detecta el fallo y
usa automaticamente recuperacion lexical.

Comprueba todo:

```powershell
python tools\test_connections.py
```

Debes ver algo parecido a:

```text
Ollama chat   : OK
Embeddings    : OK
MySQL         : OK
Memory Cortex : OK
```

Si bge-m3 todavia no esta instalado:

```text
Embeddings    : FALLBACK LEXICAL
```

Eso no es un error critico.

Inicia EVA:

```powershell
python app.py
```

Abre:

```text
http://127.0.0.1:5000
```

## Migracion de base de datos

No importes SQL manualmente.

La primera ejecucion crea o migra automaticamente:

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
+-- entities
+-- entity_relations
+-- memory_tree
+-- tasks
```

La tabla memories recibe ademas:
- embedding
- strength
- content_hash
- updated_at

Los datos v0.3 se conservan.

## Diagnostico

Estado cognitivo completo:

```powershell
python tools\inspect_eva.py
```

Endpoints:

```text
http://127.0.0.1:5000/api/cognition
http://127.0.0.1:5000/api/memory/tree
http://127.0.0.1:5000/api/system
```

`/api/system` permite revisar:
- estado del Memory Cortex
- modelo de embeddings
- ultimo error de embeddings
- cola del Archivist
- turnos archivados
- heartbeat

## Configuracion v0.4

Las opciones nuevas estan en `.env.example`.

Principales:

```text
EVA_EMBEDDINGS_ENABLED=true
EVA_EMBEDDING_MODEL=bge-m3

EVA_ARCHIVIST_ENABLED=true
EVA_ARCHIVIST_MODEL=qwen3:1.7b

EVA_HEARTBEAT_ENABLED=false
EVA_AUTONOMY_ENABLED=false
```

En el Acer con 8 GB se recomienda mantener:
- Qwen3 1.7B para chat y Archivist
- bge-m3 para embeddings
- heartbeat desactivado mientras probamos estabilidad

## Prueba recomendada

Dile:

```text
Recuerda que mi bebida favorita es el cafe.
Mi proyecto principal se llama EVA.
EVA usa Ollama y MySQL.
```

Espera unos segundos para permitir que el Archivist termine.

Luego:

```text
Que bebida prefiero?
Que proyecto estamos desarrollando?
Que tecnologias usa EVA?
```

Finalmente:

```powershell
python tools\inspect_eva.py
```

Deberias comenzar a ver:
- recuerdos
- ramas del Memory Tree
- entidades
- estado del motor semantico

## Arquitectura v0.4

```text
Usuario
  |
  v
EVA Agent
  |
  +--> Emotion Engine
  |
  +--> Memory Cortex
  |      |
  |      +--> memoria lexical
  |      +--> bge-m3 embeddings
  |      +--> Memory Tree
  |      +--> entities
  |      +--> relations
  |
  +--> Qwen3 1.7B
  |
  +--> respuesta visible
  |
  +--> Post-Turn Archivist
           |
           +--> memories
           +--> identity
           +--> entities
           +--> relations
           +--> goals

Event Bus
  |
  +--> user_message
  +--> assistant_message
  +--> post_turn_archived
  +--> heartbeat
```

## Siguiente etapa

La base para v0.5 queda preparada para:
- autonomia controlada
- Goal/Task Board
- reflexion programada
- scheduler
- Tool Registry
- Security/Approval Gate
- agentes especializados
- voz neural local
- STT por microfono
- sincronizacion labial con audio real
