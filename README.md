# IAMO

Repositorio histórico de una de las primeras exploraciones de **IAMO** dentro de DesarrollAMO: coordinación de objetivos, bloques y roles para construir una relación más directa entre humano, software e inteligencia artificial.

## Estado

**Prototipo conceptual histórico.** El nombre IAMO sigue siendo relevante para la visión actual de DesarrollAMO, pero este código de 2025 no representa por sí solo la implementación moderna ni el proyecto IAMO OS planteado posteriormente.

## Qué contiene este snapshot

- `CreaBloques.py` — creación/organización de bloques;
- `director.py` — rol de dirección/orquestación temprana;
- `consejero.py` — placeholder de rol consultivo;
- `objetivos.json` — objetivos persistidos;
- `bloques/` — unidades modulares;
- `data/` — datos de la etapa;
- `.github/` — automatización/CI histórica;
- `requirements.txt`.

## Idea que permanece

IAMO no se entiende solamente como “otra IA”. La idea actual es una **interfaz/puerta entre la persona y capacidades inteligentes**, donde el usuario mantiene objetivos, control, privacidad y posibilidad de elegir herramientas/proveedores.

```text
Humano
  ↕
IAMO
  ↕
modelos · agentes · herramientas · dispositivos
```

## Relación con DAMO

IAMO y DAMO no son sinónimos:

- **IAMO** representa la interfaz/concepto humano ↔ IA.
- **DAMO** representa la capa ejecutora/orquestadora de DesarrollAMO.

Este repositorio antecede a varias ideas posteriores y debe conservarse como referencia, no como fuente de verdad del DAMO actual.

## Ejecución

El código es experimental. Antes de ejecutarlo o extenderlo, revisar dependencias y los datos persistidos. No hay garantía de compatibilidad actual.

## Seguridad

No guardar claves de modelos, tokens ni credenciales en `objetivos.json`, `data/`, bloques o código. La configuración sensible debe permanecer fuera del repositorio.

---

**DesarrollAMO** · IAMO es la puerta; las herramientas detrás de ella pueden evolucionar.
