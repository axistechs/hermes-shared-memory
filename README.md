# Hermes Shared Memory Skill

Sistema de memoria compartida vía SQLite para agentes Hermes. Permite que diferentes instancias (Terminal, Gateway, Telegram) compartan contexto sin estar en la misma sesión.

## Instalación rápida

```bash
# Clonar el repo
git clone https://github.com/TU_USUARIO/hermes-shared-memory.git

# Copiar a las skills de Hermes
cp -r hermes-shared-memory ~/.hermes/skills/shared-memory

# Verificar
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py stats
```

## Uso

```bash
# Agregar memoria
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py add "Algo importante" --source terminal --tags "importante"

# Buscar
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py search "importante"

# Ver contexto reciente
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py context --limit 10

# Estadísticas
python3 ~/.hermes/skills/shared-memory/scripts/shared_memory.py stats
```

## Estructura

```
shared-memory/
├── SKILL.md                  # Documentación e instrucciones para el agente
├── README.md                 # Este archivo
├── LICENSE                   # Licencia MIT
├── install.sh                # Script de instalación
├── scripts/
│   └── shared_memory.py      # Backend SQLite
└── examples/
    └── session-summary.md    # Ejemplo de resumen de sesión
```

## Base de datos

- **Ubicación:** `~/.hermes/shared-memory/memory.db`
- **Modo:** WAL (lecturas concurrentes seguras)
- **Compatible con:** Múltiples agentes simultáneamente

## Licencia

MIT
