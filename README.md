<div align="center">

# IAMO

### Interfaz humano ↔ inteligencia

**Una puerta para conectar objetivos humanos con modelos, agentes, herramientas y dispositivos sin entregarles la propiedad del sistema.**

[🏢 Ver oficina](https://github.com/amoedo7/landings/blob/main/oficinas.html#iamo-damo) · [🌐 DesarrollAMO](https://desarrollamo.com.ar/) · [🗺️ Ecosistema](https://github.com/amoedo7/amoedo7)

</div>

---

## Estado de este repositorio

**Prototipo conceptual histórico.** El nombre IAMO sigue siendo parte de la visión actual de DesarrollAMO, pero este código de 2025 no representa por sí solo la implementación moderna ni el IAMO OS imaginado después.

El repositorio se conserva porque documenta una etapa temprana importante: objetivos persistentes, bloques, roles y una interfaz más directa entre persona, software e inteligencia artificial.

## La idea que permanece

```text
                         HUMANO
                           ↕
                          IAMO
                           ↕
      ┌────────────────────┼────────────────────┐
      │                    │                    │
   modelos              agentes             herramientas
      │                    │                    │
      └────────────────────┼────────────────────┘
                           ↕
                    datos / dispositivos
```

IAMO no debería convertirse en “otra IA que decide todo”. Su función conceptual es ser la **interfaz y capa de control del usuario**.

### Principios

- objetivos del usuario por encima del proveedor;
- memoria útil y controlable;
- privacidad fuerte;
- modelos intercambiables;
- agentes con capacidades y límites claros;
- trazabilidad de acciones;
- posibilidad de trabajar con IA local o remota;
- ningún proveedor debe convertirse en dueño de los datos o del proceso.

## IAMO y DAMO no son lo mismo

| Capa | Rol |
|---|---|
| **IAMO** | interfaz/concepto humano ↔ IA |
| **DAMO** | ejecutor/orquestador operativo de DesarrollAMO |
| **EstructurAMO** | organización, ownership, prioridades y gobernanza |

La relación conceptual puede verse así:

```text
Persona
  ↓
IAMO
  ↓
EstructurAMO
  ↓
DAMO / oficinas / herramientas
  ↓
resultado verificable
```

## Qué contiene este snapshot

- `CreaBloques.py` — creación y organización de bloques;
- `director.py` — rol de dirección/orquestación temprana;
- `consejero.py` — placeholder de rol consultivo;
- `objetivos.json` — objetivos persistidos;
- `bloques/` — unidades modulares;
- `data/` — datos de aquella etapa;
- `.github/` — automatización/CI histórica;
- `requirements.txt`.

## Regla de evolución

No reactivar este repositorio suponiendo que representa el IAMO actual. Si una idea vuelve a ser útil:

`inspeccionar → rescatar → adaptar → probar → documentar`

No copiar la arquitectura histórica por nostalgia.

## Seguridad

No guardar claves de modelos, tokens ni credenciales en `objetivos.json`, `data/`, bloques o código. La configuración sensible debe permanecer fuera del repositorio.

---

<div align="center">

**DesarrollAMO** · IAMO es la puerta; las herramientas detrás pueden evolucionar.

</div>
