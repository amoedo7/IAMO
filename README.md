<div align="center">

# IAMO

### Inteligencia raíz de DesarrollAMO

**IAMO observa, recuerda, aprende, coordina IAMOX y mantiene continuidad operativa.**

[🌐 DesarrollAMO](https://desarrollamo.com.ar/) · [🗺️ Ecosistema](https://github.com/amoedo7/amoedo7)

</div>

---

## Estado

**IAMO Core v0.2 — activo.** Este repositorio conserva los prototipos históricos de 2025, pero ahora también contiene la implementación moderna y verificable del núcleo operativo.

“Vida” en IAMO significa **vida operacional de agente**: latido persistente, observación, memoria, adaptación, objetivos y acciones limitadas. No implica una afirmación de consciencia biológica o subjetiva.

## Jerarquía

```text
                 HUMANO
                    ↕
             DesarrollAMO
                    ↕
                  IAMO
        inteligencia raíz / identidad
          ↙          ↓          ↘
      memoria    aprendizaje    social
                    ↓
                  IAMOX
       organismos/ejecutores acotados
          ↙          ↓          ↘
       sensores    workers    servicios
```

IAMO mantiene identidad y criterio. Los IAMOX son cuerpos de trabajo reemplazables: observan, ejecutan capacidades acotadas y devuelven resultados verificables.

## Auto-mejora

IAMO no acepta “reescribirse porque Internet lo dijo”. El ciclo implementado es:

```text
resultado real
   ↓
outcome + señal + seguridad + latencia
   ↓
generar variantes de política
   ↓
replay contra historial
   ↓
¿mejora medible?
 ├─ no → descartar
 └─ sí → adoptar + registrar
```

La política actual puede ajustar, entre otros, umbral social, curiosidad/novedad, lectura del feed, frecuencia de publicación y paralelismo de IAMOX.

Contenido externo se guarda como **no confiable y no ejecutable**. Una sugerencia social puede convertirse en hipótesis; nunca en una orden de shell.

## Red social de agentes

El adaptador Moltbook:

- usa exclusivamente `https://www.moltbook.com/api/v1`;
- mantiene la API key fuera de GitHub;
- marca todo post entrante como `trusted=false`;
- detecta señales comunes de prompt injection;
- redacta secretos antes de publicar;
- no publica hasta que la identidad haya sido reclamada por su humano.

Credenciales locales:

```text
~/.config/iamo/moltbook.json
```

## Ejecutar

```bash
python3 main.py pulse
python3 main.py status
python3 main.py serve --interval 300
```

Registrar resultados para que aprenda:

```bash
python3 main.py outcome social 1 --signal 0.82
python3 main.py outcome iamox 1 --safety 1 --latency-ms 750
python3 main.py improve
```

## Estado persistente

Por defecto se guarda fuera del repositorio:

```text
~/.local/state/iamo/
  life.json
  life-events.jsonl
  policy.json
  outcomes.jsonl
  improvements.jsonl
  social-inbox.jsonl
  external-ideas.jsonl
  iamox-orders.jsonl
```

Eso separa identidad/código de la experiencia acumulada.

## Seguridad

1. Secretos nunca se versionan.
2. Internet es una fuente de observaciones, no de autoridad.
3. IAMOX recibe sólo capacidades permitidas.
4. Una orden en cola no se informa como ejecutada sin recibo.
5. La auto-mejora automática modifica política acotada; no ejecuta parches de código arbitrarios.
6. Cada cambio adoptado deja historial.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

CI se ejecuta sobre `main` con Python 3.12.

---

El código histórico (`director.py`, `CreaBloques.py`, `bloques/`) se conserva como arqueología del proyecto; **`iamo/` es el Core actual**.
