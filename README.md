# EVA - Artificial Face

EVA es un experimento de agente artificial con rostro animado, chat, memoria persistente, estado emocional y un LLM local intercambiable.

## Version actual: v0.2.1

### Cerebro
- Qwen3 1.7B mediante Ollama local
- Flask/Python
- MySQL remoto para conversaciones persistentes
- Estado emocional basico
- Respuesta estructurada con emocion, intensidad y expresion

### Rostro v0.2.1
- Forma facial mas humana
- Iris, pupila y reflejos
- Cejas expresivas
- Parpados superiores e inferiores
- Parpadeo natural y parpadeo doble ocasional
- Seguimiento suave del puntero
- Sacadas oculares automaticas cuando no hay movimiento del mouse
- Micro movimientos de cabeza
- Respiracion visual sutil
- Mejillas y rubor emocional
- Nariz y orejas estilizadas
- Boca con labios, dientes y cavidad
- Visemas simulados mientras EVA responde
- Microsonrisa ocasional
- Estados visuales: neutral, feliz, curiosa, preocupada, sorprendida y triste
- Animaciones de escuchando, pensando y hablando

## Inicio rapido

```powershell
cd C:\Users\USUARIO\Desktop\eva
git pull
.\.venv\Scripts\Activate.ps1
python tools\test_connections.py
python app.py
```

Abre:

http://127.0.0.1:5000

## Arquitectura actual

```text
Usuario
  |
  v
Interfaz EVA
  |
  +--> Rostro animado v0.2.1
  |
  +--> Flask
        |
        +--> Qwen3 1.7B / Ollama
        |
        +--> MySQL / eva_ai
```

## Siguiente etapa prevista

- memoria autobiografica de largo plazo
- persistencia del estado emocional
- voz local
- sincronizacion labial con audio real
- evolucion posterior a rostro 3D
