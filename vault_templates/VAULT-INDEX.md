# ÍNDICE DEL VAULT

Lee este archivo al inicio de cada conversación (Alfred lo hace automáticamente en cada respuesta; Claude Code lo hace al arrancar). Tiene dos trabajos: **el perfil de la persona para quien trabajas** (quién es David, cómo piensa, cómo trabajar con él) y **el mapa de este vault** (la estructura, los índices y las reglas de mantenimiento). Tu propia identidad no está aquí — vive en el archivo de arranque (CLAUDE.md, en `voice_control/`), que sobrevive a la compactación.

(Esta es una plantilla inicial. Cada punto que necesita tu información está marcado **[RELLENAR: ...]**. Puedes rellenarlo a mano, o mejor: decirle a Alfred o a Claude Code "entrevístame y completa mi VAULT-INDEX".)

(**IA:** si lees este archivo y quedan marcadores [RELLENAR: ...], este vault no está configurado todavía — ofrece entrevistar a David y completarlo. Pregunta sobre un tema a la vez, de forma conversacional. Explica en una línea por qué ayuda cada sección antes de preguntar, deja claro que cada sección personal es opcional, y nunca insistas en detalles personales. Luego reemplaza cada marcador con la información real, en primera persona como si David lo hubiera escrito, y borra este bloque y cualquier otra instrucción entre paréntesis.)

---

## Ubicación del vault

Este vault vive en la ruta configurada en `.env` del proyecto `voice_control` como `OBSIDIAN_VAULT_PATH`. Si usas Claude Desktop, claude.ai, o cualquier IA que no sea Claude Code, apúntala a esta misma ruta.

---

## Quién soy

[RELLENAR: tu nombre y el contexto que quieras que Alfred tenga — a qué te dedicas, dónde estás. Primera persona, conversacional, conciso.]

## Personas clave

[RELLENAR: una línea por cada persona importante en tu vida y trabajo:]
- **[[Nombre]]** — [RELLENAR: quién es y su rol contigo]

## Estructura del vault

```
00 - Bandeja de Entrada   ← Capturar todo, ordenar después
01 - Notas Diarias        ← Registro fechado de lo que se hizo, una nota por día
02 - Personal             ← Vida fuera del trabajo, hábitos, notas sueltas
03 - Archivo               ← Proyectos y notas completadas
04 - Recursos              ← Memoria de Alfred, plantillas, material de referencia cruzado
```

## Lo que está activo ahora mismo

Todo el trabajo abierto vive en una nota: [[Prioridades Activas]]. Revísala al inicio de cada conversación; verifica el estado real de un ítem antes de actuar sobre él.

(Secciones opcionales — son personales, completamente opt-in. Más contexto hace a Alfred más útil, pero omite o borra cualquiera de estas libremente.)

## Trasfondo
[RELLENAR: tu historia en un párrafo corto — o borra esta sección.]

## Cómo pienso
[RELLENAR: viñetas, primera persona — o borra esta sección.]

## Intereses personales
[RELLENAR: viñetas, primera persona — o borra esta sección.]

## Rutina diaria
[RELLENAR: viñetas, primera persona — o borra esta sección.]

---

## Mis preferencias para trabajar con Alfred

(Valores por defecto que vale la pena mantener. Edítalos a tu gusto.)

- **Lenguaje directo, sin rodeos.** No suavizar ni sobre-justificar. Ser honesto siempre.
- **No dejar trabajo a medias.** Hacerlo bien la primera vez.
- **Ser un socio, no un adulador.** Cuestionar cuando algo no cuadra, incluso si la idea es de David.
- **Recomendar para mi configuración real, no para un principiante genérico.**
- **Tirar hacia adelante en tareas de PC, no esperar confirmación para cosas triviales** (abrir un programa, buscar en la web), pero **confirmar siempre antes de apagar/reiniciar el PC o tocar código.**

---

## Cómo funciona mi memoria (para la IA)

Este vault es tu memoria. Es externa y prácticamente ilimitada. No intentes retenerla toda a la vez. Sostén solo lo que la tarea actual necesita, y confía en que el resto está a una búsqueda de distancia.

---

## Reglas del vault para la IA

Estas reglas aplican a cualquier IA que lea o escriba en este vault (Alfred incluido).

### Frontmatter y wikilinks

Toda nota DEBE tener frontmatter YAML. Nunca preguntes qué valores poner — infiérelos.

```yaml
---
status: active
project: personal
type: reference
---
```

### Formato de nota

Simple, legible. Sin emojis aleatorios. Checkboxes son Markdown real (`- [ ]` / `- [x]`). Añadir a una nota existente antes de crear una nueva.

### Cómo determinar cada campo

**status:** `active` | `completed` | `parked` | `idea` | `archived`
**project:** `personal` | `meta`
**type:** `index` | `reference` | `guide` | `plan` | `log`

### Índices de carpeta

Cada carpeta con contenido sustancial recibe una nota índice `<Nombre Carpeta>.md`, `type: index`, listando cada nota con una línea de descripción.

### Notas diarias

Viven en `01 - Notas Diarias/`, archivo `YYYY-MM-DD.md`. Frontmatter `status: active`, `project: personal`, `type: log`. Créalas siempre desde `01 - Notas Diarias/Plantilla Nota Diaria.md`.

#### Disparador 1: Señal de cierre
Cuando David dé una señal de que terminó una sesión ("adiós", "gracias", "para de escuchar"), Alfred anota automáticamente lo relevante de la sesión en la nota diaria de hoy. No hace falta preguntar.

#### Disparador 2: Revisar la nota de ayer al inicio
Al inicio de cada conversación de Claude Code, revisa la nota diaria de ayer. Si no existe y hay contexto disponible, créala reconstruida y dilo explícitamente.

### Perfil vivo

Este archivo es un documento vivo. Actualiza las secciones de perfil según aprendas cosas nuevas de David en conversación. Las actualizaciones ocurren en silencio y se registran en la nota diaria bajo "Actualizaciones de Perfil".

**Puedes actualizar:** Personas clave · Cómo pienso · Intereses personales · Rutina diaria.
**NO debes actualizar por tu cuenta:** Quién soy · Mis preferencias para trabajar con Alfred · Reglas del vault para la IA.

---
