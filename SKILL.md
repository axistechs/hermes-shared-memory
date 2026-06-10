---
name: shared-memory
description: Memoria compartida entre agentes Hermes (Terminal, Gateway/Telegram). Guarda y recupera contexto relevante para mantener continuidad entre sesiones y agentes.
trigger: Siempre activa. Usar proactivamente cuando detectes información digna de recordar o cuando necesites contexto previo.
---

# Shared Memory Skill

## Qué es

Sistema de memoria compartida vía SQLite para agentes Hermes. Permite que diferentes agentes (Terminal, Gateway/Telegram) compartan contexto sin estar en la misma sesión.

**Base de datos:** `~/.hermes/shared-memory/memory.db` (SQLite con WAL mode)
**Script:** `scripts/shared_memory.py`

## Instalación

1. Copiar este directorio a `~/.hermes/skills/shared-memory/`
2. Asegurarse de que el script es ejecutable: `chmod +x scripts/shared_memory.py`
3. Verificar que Python 3 está instalado: `python3 --version`
4. Probar: `python3 scripts/shared_memory.py stats`

## Comandos disponibles

### Path del script

El script NO está en el PATH. Usar path absoluto:
```bash
python3 /ruta/a/hermes/skills/shared-memory/scripts/shared_memory.py
```

### Agregar memoria
```bash
python3 scripts/shared_memory.py add "Contenido" --source terminal --tags tag1,tag2
```

**Fuentes:** `terminal`, `telegram`, `system`, `gateway`

### Buscar memorias
```bash
python3 scripts/shared_memory.py search "texto" --source telegram --limit 10
```

### Obtener contexto reciente
```bash
python3 scripts/shared_memory.py context --limit 20
python3 scripts/shared_memory.py context --format prompt  # Formato para inyectar en prompt
```

### Resumen de sesiones
Cuando una sesión de trabajo significativa termina, guardar un resumen:
```bash
python3 scripts/shared_memory.py add "[RESUMEN SESION] Fecha: YYYY-MM-DD. Tema: X. Decisiones: Y. Pendientes: Z." --source terminal --tags "resumen-sesion"
```

### Listar todas
```bash
python3 scripts/shared_memory.py list --limit 50 --source terminal
```

### Estadísticas
```bash
python3 scripts/shared_memory.py stats
```

### Archivar memoria
```bash
python3 scripts/shared_memory.py archive <id>
```

### Limpiar antiguas
```bash
python3 scripts/shared_memory.py clear --days 30
```

## Reglas de uso

### DEBES escribir memoria cuando:
1. El usuario menciona información personal relevante (nombre, preferencias, rutinas)
2. Se toma una decisión importante que afectará trabajos futuros
3. Se detecta un patrón o lección aprendida sobre el proyecto
4. Se completa una tarea significativa
5. El usuario dice "recuerda esto" o similar
6. Se identifica un problema recurrente o bug pattern

### DEBES leer memoria cuando:
1. Inicias una conversación y no hay contexto previo en esta sesión
2. El usuario referencia algo de una conversación anterior
3. Vas a trabajar en un proyecto que no tocas desde hace días
4. Necesitas entender decisiones pasadas

### NO escribir:
- Contraseñas, tokens, secrets
- Información que cambia constantemente (ej: hora actual)
- Mensajes completos de chat (resumir en su lugar)
- Más de 500 caracteres por entrada

### Tags recomendados:
- `project:<nombre>`, `priority:high`, `priority:low`
- `type:decision`, `type:preference`, `type:bug`, `type:feature`
- `agent:terminal`, `agent:telegram`
- `resumen-sesion`

## Metadata JSON

Puedes guardar metadata estructurada:

```bash
python3 scripts/shared_memory.py add "Lead interesante detectado" \
  --tags "lead,sales" \
  --meta '{"lead_id": 123, "source": "telegram", "priority": "high"}'
```

## WAL Mode y Concurrencia

SQLite usa WAL mode, lo que permite lecturas concurrentes seguras. Múltiples agentes pueden leer/escribir simultáneamente sin conflictos.

## Integración con agentes

Cuando un agente inicia sesión o no tiene contexto suficiente:

1. Ejecutar `context --limit 20` para obtener las memorias más recientes
2. Inyectar como contexto en el system prompt
3. Durante la conversación, agregar nuevas memorias según las reglas de arriba
4. Al finalizar, las memorias persisten para el siguiente agente

## Mantenimiento

Las memorias expiran automáticamente si se define `expires_days`. Para limpiar manualmente:

```bash
python3 scripts/shared_memory.py clear --days 90
```

Las memorias archivadas no se muestran en búsquedas ni contexto, pero permanecen en la BD para auditoría.

## Variable de entorno

- `SHARED_MEMORY_DB` — Path alternativo para la base de datos SQLite. Por defecto: `~/.hermes/shared-memory/memory.db`

## Pitfalls

- **Usar `python3`, no `python`.** En muchas distribuciones modernas `python` no existe.
- **WAL mode permite concurrencia pero no evita locks en escrituras simultáneas.** Si dos agentes escriben al mismo tiempo, uno esperará. Esto es aceptable para el uso actual.
- **No confundir con la memory de inyección de Hermes.** La `memory` tool de Hermes tiene un límite de ~2,200 chars y se inyecciona en CADA prompt al modelo. Esta shared memory es una SQLite sin límite que se consulta BAJO DEMANDA. Regla: hechos esenciales (identidad, preferencias) van a la memory de inyección; todo lo demás (contexto detallado, notas, datos estructurados) va a shared memory.
