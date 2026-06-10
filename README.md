# 🧠 Hermes Shared Memory Skill

> **Porque los agentes de IA tambien merecen recordar.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-3.x-green.svg)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-orange.svg)](https://sqlite.org)

---

## 🤔 ¿Que es esto?

¿Alguna vez le dijiste algo importante a tu agente de IA... y al dia siguiente no tenia ni la mas minima idea de lo que hablaron? **Frustrante, ¿verdad?**

**Hermes Shared Memory Skill** es la solucion: un sistema de memoria compartida via SQLite que permite que diferentes agentes Hermes (Terminal, Gateway, Telegram) **compartan contexto** sin importar si estan en la misma sesion o no.

Piensalo como una **sala de reuniones virtual** donde todos los agentes dejan notas, leen lo que otros escribieron, y nadie se queda fuera de la conversacion.

### ¿Que problema resuelve?

| Sin Shared Memory | Con Shared Memory |
|---|---|
| Cada sesion empieza de cero | El contexto persiste entre sesiones |
| El agente Terminal no sabe que dijo el de Telegram | Todos los agentes comparten la misma memoria |
| Repites la misma info una y otra vez | La info se guarda una sola vez y se consulta cuando se necesita |
| Pierdes decisiones importantes | Todo queda registrado con tags, fechas y metadata |

---

## 🚀 Instalacion rapida

### Opcion A: Script automatico (recomendado)

```bash
# Clonar el repo
git clone https://github.com/axistechs/hermes-shared-memory.git

# Ejecutar instalador
cd hermes-shared-memory
bash install.sh
```

### Opcion B: Manual

```bash
# Clonar
git clone https://github.com/axistechs/hermes-shared-memory.git

# Copiar a las skills de Hermes
cp -r hermes-shared-memory ~/.hermes/skills/shared-memory

# Dar permisos al script
chmod +x ~/.hermes/skills/shared-memory/scripts/shared_memory.py

# Verificar
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py stats
```

¡Listo! La base de datos se crea automaticamente en `~/.hermes/shared-memory/memory.db`.

---

## 📖 Uso

### Agregar memoria

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py add \
  "El usuario prefiere respuestas en español y con explicaciones detalladas" \
  --source terminal \
  --tags "preferencia,idioma"
```

### Buscar memorias

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py search "español"
```

Output:
```
  [3] (terminal) El usuario prefiere respuestas en español... [preferencia,idioma]
```

### Ver contexto reciente

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py context --limit 10
```

### Formato para inyectar en prompt del agente

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py context --limit 20 --format prompt
```

Output:
```
## Contexto compartido (memorias recientes):
- [terminal] El usuario prefiere respuestas en español (2026-06-10)
- [telegram] Reunión con cliente X programada para mañana (2026-06-09)
```

### Estadisticas

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py stats
```

Output:
```
Total activas: 42
Ultimos 7 dias: 15
Por fuente:
  terminal: 28
  telegram: 14
```

### Resumenes de sesion

Cuando una sesion importante termina, guarda un resumen:

```bash
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py add \
  "[RESUMEN SESION] Fecha: 2026-06-10. Tema: Configuracion de memoria compartida. Decisiones: Memory corta para identidad/preferencias, shared memory para todo lo operativo. Pendientes: Probar con Hermes Windows." \
  --source terminal \
  --tags "resumen-sesion"
```

### Mantenimiento

```bash
# Archivar memorias de mas de 90 dias
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py clear --days 90

# Archivar una memoria especifica por ID
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py archive 5
```

---

## 🗂️ Estructura del proyecto

```
hermes-shared-memory/
├── SKILL.md                  # Documentacion completa e instrucciones para el agente
├── README.md                 # Este archivo (si, el que estas leyendo)
├── LICENSE                   # Licencia MIT
├── install.sh                # Instalador automatico
├── .gitignore                # Excluye memory.db y archivos locales
└── scripts/
    └── shared_memory.py      # El motor: backend SQLite con WAL mode
```

---

## 🧠 Arquitectura de memoria: Dos niveles

Esta skill esta diseñada para trabajar en conjunto con la memoria nativa de Hermes, no para reemplazarla.

### Nivel 1 — Memory de inyeccion (corta, ~2,200 chars)
Se inyecta en **cada mensaje** al modelo. Debe ser minima:
- Identidad del usuario (¿quien es?)
- Preferencias de comunicacion (¿como le gusta que le hable?)
- Reglas fundamentales (¿que siempre debe recordar?)

### Nivel 2 — Shared Memory (SQLite, sin limite)
Se consulta **bajo demanda**. Aqui va todo lo demas:
- Contexto detallado del proyecto
- Decisiones tecnicas con justificacion
- Lecciones aprendidas entre sesiones
- Resumenes de conversaciones anteriores
- Datos estructurados (leads, reuniones, bugs, patrones)

### La regla de oro

> **Si cabe en una frase corta → Memory de inyeccion.**
> **Si es detallado, tecnico o voluminoso → Shared Memory.**

---

## 🔧 Referencia de la API CLI

| Comando | Descripcion | Ejemplo |
|---------|-------------|---------|
| `add` | Agregar memoria | `add "Contenido" --source terminal --tags "tag1,tag2"` |
| `search` | Buscar por texto | `search "texto" --source telegram --limit 10` |
| `context` | Contexto reciente | `context --limit 20 --format prompt` |
| `list` | Listar todas | `list --source terminal --limit 50` |
| `stats` | Estadisticas | `stats` |
| `archive` | Archivar por ID | `archive 5` |
| `clear` | Limpiar antiguas | `clear --days 90` |

### Fuentes disponibles

- `terminal` — Sesion de terminal
- `telegram` — Bot de Telegram
- `gateway` — Gateway de Hermes
- `system` — Sistema automatico
- `unknown` — Sin fuente especifica

### Metadata JSON

Puedes adjuntar datos estructurados a cualquier memoria:

```bash
python3 scripts/shared_memory.py add "Lead calificado" \
  --tags "lead,sales" \
  --meta '{"lead_id": 123, "valor": 5000, "moneda": "USD"}'
```

---

## 🌐 Variable de entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `SHARED_MEMORY_DB` | Path alternativo para la BD | `~/.hermes/shared-memory/memory.db` |

Util si quieres compartir la misma base de datos entre diferentes maquinas via un disco compartido.

---

## ⚠️ Lo que NUNCA debes guardar aqui

- ❌ Contraseñas o tokens
- ❌ API keys o secrets
- ❌ Informacion financiera sensible
- ❌ Datos que cambian cada minuto (usar la memory de inyeccion para eso)

---

## 🛡️ Seguridad

- La base de datos es un archivo SQLite local. **No se envia a ningun servidor.**
- El `.gitignore` excluye `memory.db` para que nunca se suba al repo.
- El token de GitHub usado para crear el repo **no se almacena** en ningun archivo.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar la skill:

1. Haz un fork del repo
2. Crea una rama (`git checkout -b feature/mi-mejora`)
3. Haz commit (`git commit -m "Agrega mi mejora"`)
4. Haz push (`git push origin feature/mi-mejora`)
5. Abre un Pull Request

---

## 📜 Licencia

[MIT](LICENSE) — Haz lo que quieras con esto, solo no culpes a los autores si algo sale mal. 😄

---

## 🙏 Creditos

Creado con ❤️ por [Axistechs](https://github.com/axistechs) para la comunidad de Hermes Agent.

**Recuerda:** Un agente sin memoria es como un desarrollador sin git — tecnicamente posible, pero ¿para que sufrir?

---

<p align="center">
  <i>Hecho con cafe, SQLite y la firme creencia de que los agentes de IA merecen recordar.</i>
</p>
