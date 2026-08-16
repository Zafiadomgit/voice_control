# Memoria de Alfred en Obsidian

Alfred ya no guarda su memoria en `memoria.json`. Ahora vive en un **vault de
Obsidian** — una carpeta de notas Markdown que tú controlas, sigues con
Git si quieres, y puedes abrir con la app de [Obsidian](https://obsidian.md).
El diseño está tomado de [ai-memory-vault](https://github.com/jaredrhod/ai-memory-vault).

## Qué hace cada pieza

- **`CLAUDE.md`** (en esta carpeta) — el archivo de arranque. Define la
  identidad de Alfred y las reglas que no caducan. Lo carga Claude Code
  automáticamente cuando Alfred lo abre por voz desde este proyecto.
- **`obsidian_vault.py`** — el código que `asistente.py` usa para leer y
  escribir en el vault (nombre, preferencias, notas, resumen de
  conversaciones, notas diarias).
- **`vault_templates/`** — plantillas que se copian DENTRO del vault la
  primera vez (`VAULT-INDEX.md`, la plantilla de nota diaria, `MEMORY.md`).
- **`setup_obsidian.py`** — script de configuración inicial, crea la
  estructura de carpetas del vault.
- **`config_local.json`** (se genera solo, no se versiona) — configuración
  puramente operativa que NO es memoria: programas guardados por voz,
  hábitos detectados. Esto se queda local, fuera del vault.

## Configuración (una sola vez)

1. Elige o crea una carpeta para tu vault, por ejemplo
   `C:\Users\david\Documents\Vault`.
2. Añádela a tu `.env`:
   ```
   OBSIDIAN_VAULT_PATH=C:\Users\david\Documents\Vault
   ```
3. Corre:
   ```
   python setup_obsidian.py
   ```
   Esto crea la estructura de carpetas y copia `VAULT-INDEX.md`, la
   plantilla de nota diaria y la nota `Memoria Alfred.md`.
4. Abre esa carpeta como vault en la app de Obsidian.
5. Arranca Alfred (`python asistente.py`) y dile algo como *"Alfred,
   entrevístame y completa mi VAULT-INDEX"*, o ábrelo con Claude Code desde
   esta carpeta y pide lo mismo — así se rellenan los `[RELLENAR: ...]` del
   perfil (quién eres, gente clave, tus preferencias).

Si no configuras `OBSIDIAN_VAULT_PATH`, Alfred sigue funcionando igual,
solo que sin memoria persistente de nombre/preferencias/notas entre
sesiones (la config operativa en `config_local.json` sí se guarda).

## Qué pasa mientras usas Alfred

- Cuando le pides que recuerde algo ("me llamo David", "prefiero
  resultados en español", "recuerda que trabajo de noche"), lo escribe en
  `04 - Recursos/Memoria Alfred.md` dentro del vault.
- Al terminar una sesión de voz (decir "adiós", "gracias", etc., o cerrar
  Alfred con Ctrl+C), si hubo algo nuevo que recordar, se anota en la nota
  diaria de hoy (`01 - Notas Diarias/YYYY-MM-DD.md`).
- En cada respuesta, Alfred vuelve a leer `VAULT-INDEX.md` y
  `Memoria Alfred.md`, así que cualquier cosa que edites a mano en Obsidian
  (o que complete Claude Code en una sesión de texto) también lo sabe la
  próxima vez que le hables.
