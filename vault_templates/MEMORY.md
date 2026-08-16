<!-- Plantilla inicial para el tutorial de memoria en Obsidian, adaptada al proyecto voice_control (Alfred).

Este es el archivo de memoria PROPIO de Claude Code (no de Alfred). NO va dentro del vault — vive en la carpeta de proyecto de Claude Code, bajo ~/.claude/projects/. La subcarpeta se llama como la carpeta desde la que corres Claude Code (tu directorio de trabajo, ej. voice_control), con las barras convertidas en guiones — así que la forma más simple es buscarla: corre  ls ~/.claude/projects/  y abre la carpeta que coincide con voice_control, o pregúntale a Claude Code "¿dónde está tu archivo MEMORY.md?"

Reemplazar el contenido de ese archivo con el puntero de abajo hace que la memoria nativa de Claude Code redirija a tu vault, para que nunca termines con dos capas de memoria que se desincronizan. Migra primero cualquier cosa que ya esté ahí a tu vault, y luego pega esto. -->

No hay una capa de memoria separada aquí. La única fuente de verdad es el vault de Obsidian, cuya ruta está en el archivo `.env` del proyecto `voice_control`, variable `OBSIDIAN_VAULT_PATH`.

Lee el vault desde esa ruta al inicio de cada sesión. Orden de carga:
- CLAUDE.md (en `voice_control/`, la carpeta desde la que corre Claude Code — NO en el vault) — configuración de arranque: identidad de Alfred + reglas que no caducan.
- VAULT-INDEX.md (en la raíz del vault) — perfil de David, reglas completas, mapa del sistema.
- Todo lo demás vive en su hogar contextual dentro del vault.

Para recordar algo, escríbelo en su lugar dentro del vault, nunca aquí.
