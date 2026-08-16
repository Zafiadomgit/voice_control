"""
OBSIDIAN VAULT — memoria externa de Alfred
===========================================
Reemplaza memoria.json para los datos "de memoria" (nombre, preferencias,
notas, resumen de conversaciones): en vez de JSON local, viven como notas
Markdown en un vault de Obsidian, siguiendo la estructura de
https://github.com/jaredrhod/ai-memory-vault

La configuración operativa (programas guardados, hábitos aprendidos) sigue
en config_local.json — no es "memoria" en el sentido del vault, es config
de la app.

Estructura del vault (ver vault_templates/ para las plantillas):
  VAULT-INDEX.md
  Prioridades Activas.md
  00 - Bandeja de Entrada/
  01 - Notas Diarias/
      Plantilla Nota Diaria.md
      YYYY-MM-DD.md
  02 - Personal/
  03 - Archivo/
  04 - Recursos/
      Memoria Alfred.md
"""

import re
from datetime import datetime
from pathlib import Path

CARPETA_DIARIO   = "01 - Notas Diarias"
CARPETA_RECURSOS = "04 - Recursos"
NOTA_MEMORIA     = "Memoria Alfred.md"
PLANTILLA_DIARIA = "Plantilla Nota Diaria.md"

DIAS_ES  = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]


class ObsidianVault:
    def __init__(self, ruta):
        self.ruta = Path(ruta)

    def existe(self):
        return self.ruta.exists() and (self.ruta / "VAULT-INDEX.md").exists()

    # ─────────────────────────────────────────
    # MEMORIA ALFRED (nombre, preferencias, notas, resumen)
    # ─────────────────────────────────────────

    def _ruta_memoria(self):
        return self.ruta / CARPETA_RECURSOS / NOTA_MEMORIA

    def cargar_memoria_alfred(self):
        mem = {"nombre": None, "preferencias": [], "notas": [], "resumen_conversacion": ""}
        ruta = self._ruta_memoria()
        if not ruta.exists():
            return mem
        try:
            texto = ruta.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[VAULT] No pude leer {ruta}: {e}")
            return mem

        nombre = self._extraer_seccion(texto, "Nombre")
        if nombre and not nombre.startswith("[RELLENAR"):
            mem["nombre"] = nombre.strip().splitlines()[0].strip() if nombre.strip() else None

        preferencias = self._extraer_seccion(texto, "Preferencias")
        if preferencias:
            mem["preferencias"] = self._extraer_bullets(preferencias)

        notas = self._extraer_seccion(texto, "Notas")
        if notas:
            mem["notas"] = self._extraer_bullets(notas)

        resumen = self._extraer_seccion(texto, "Resumen de Conversaciones Anteriores")
        if resumen and resumen.strip() not in ("", "-"):
            mem["resumen_conversacion"] = resumen.strip()

        return mem

    def guardar_memoria_alfred(self, mem):
        ruta = self._ruta_memoria()
        ruta.parent.mkdir(parents=True, exist_ok=True)

        nombre = mem.get("nombre") or ""
        preferencias = mem.get("preferencias") or []
        notas = mem.get("notas") or []
        resumen = mem.get("resumen_conversacion") or ""

        bloques = [
            "---",
            "status: active",
            "project: personal",
            "type: reference",
            "---",
            "",
            "# Memoria de Alfred",
            "",
            "<!-- Mantenida automáticamente por asistente.py. No la edites a mano mientras Alfred está corriendo — los cambios se sobrescriben. -->",
            "",
            "## Nombre",
            nombre if nombre else "[RELLENAR: aún no me lo has dicho]",
            "",
            "## Preferencias",
        ]
        bloques += [f"- {p}" for p in preferencias] if preferencias else ["-"]
        bloques += ["", "## Notas"]
        bloques += [f"- {n}" for n in notas] if notas else ["-"]
        bloques += ["", "## Resumen de Conversaciones Anteriores"]
        bloques += [resumen if resumen else "-"]
        bloques += [""]

        try:
            ruta.write_text("\n".join(bloques), encoding="utf-8")
        except Exception as e:
            print(f"[VAULT] No pude guardar {ruta}: {e}")

    # ─────────────────────────────────────────
    # PERFIL (desde VAULT-INDEX.md)
    # ─────────────────────────────────────────

    def leer_perfil(self):
        ruta = self.ruta / "VAULT-INDEX.md"
        if not ruta.exists():
            return ""
        try:
            texto = ruta.read_text(encoding="utf-8")
        except Exception:
            return ""

        partes = []
        quien_soy = self._extraer_seccion(texto, "Quién soy")
        if quien_soy and "[RELLENAR" not in quien_soy:
            partes.append("Quién es David: " + quien_soy.strip())

        personas = self._extraer_seccion(texto, "Personas clave")
        if personas and "[RELLENAR" not in personas:
            partes.append("Personas clave:\n" + personas.strip())

        preferencias_ia = self._extraer_seccion(texto, "Mis preferencias para trabajar con Alfred")
        if preferencias_ia and "[RELLENAR" not in preferencias_ia:
            partes.append("Preferencias de David para trabajar con Alfred:\n" + preferencias_ia.strip())

        return "\n\n".join(partes)

    # ─────────────────────────────────────────
    # NOTA DIARIA
    # ─────────────────────────────────────────

    def _ruta_diario_hoy(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        return self.ruta / CARPETA_DIARIO / f"{hoy}.md"

    def _encabezado_diario(self, fecha):
        dia_semana = DIAS_ES[fecha.weekday()]
        mes = MESES_ES[fecha.month - 1]
        return f"# {dia_semana.capitalize()}, {mes} {fecha.day}, {fecha.year}"

    def agregar_sesion_diaria(self, tema, hecho=None, en_progreso=None, decisiones=None,
                               notas_tocadas=None, actualizaciones_perfil=None):
        """Crea (si hace falta) la nota diaria de hoy desde la plantilla y le añade una sesión nueva."""
        ruta = self._ruta_diario_hoy()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ahora = datetime.now()

        if not ruta.exists():
            texto = (
                "---\n"
                "status: active\n"
                "project: personal\n"
                "type: log\n"
                f"created: {ahora.strftime('%Y-%m-%d')}\n"
                "---\n\n"
                f"{self._encabezado_diario(ahora)}\n\n"
                "## Índice\n\n"
            )
        else:
            try:
                texto = ruta.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[VAULT] No pude leer la nota diaria: {e}")
                return

        num_sesion = len(re.findall(r'^## Sesión \d+', texto, flags=re.MULTILINE)) + 1
        hora_txt = ahora.strftime("%I:%M %p").lstrip("0")

        # La nueva línea de índice se inserta justo antes de la primera sesión
        # (o al final si todavía no hay ninguna), así el índice queda en el
        # mismo orden cronológico que las sesiones de abajo.
        indice_linea = f"- **{tema}** — {(hecho[0] if hecho else 'sesión de voz con Alfred')}\n"
        primera_sesion = re.search(r'\n## Sesión \d+', texto)
        if primera_sesion:
            pos = primera_sesion.start()
            texto = texto[:pos] + f"\n{indice_linea}" + texto[pos:]
        elif "## Índice" in texto:
            texto = texto.rstrip("\n") + f"\n{indice_linea}"
        else:
            texto += f"\n## Índice\n\n{indice_linea}"

        def _bullets(items):
            return "\n".join(f"- {i}" for i in items) if items else "-"

        sesion = (
            f"\n## Sesión {num_sesion} — {hora_txt}: {tema}\n\n"
            "### Qué se hizo\n" + _bullets(hecho) + "\n\n"
            "### Qué sigue en progreso\n" + _bullets(en_progreso) + "\n\n"
            "### Decisiones tomadas\n" + _bullets(decisiones) + "\n\n"
            "### Notas tocadas\n" + _bullets(notas_tocadas) + "\n\n"
            "### Actualizaciones de perfil\n" + _bullets(actualizaciones_perfil) + "\n\n"
            "---\n"
        )
        texto = texto.rstrip("\n") + "\n" + sesion

        try:
            ruta.write_text(texto, encoding="utf-8")
        except Exception as e:
            print(f"[VAULT] No pude guardar la nota diaria: {e}")

    # ─────────────────────────────────────────
    # HELPERS DE PARSEO
    # ─────────────────────────────────────────

    @staticmethod
    def _extraer_seccion(texto, titulo):
        """Devuelve el contenido bajo '## {titulo}' hasta el siguiente '## ' o '---'."""
        patron = re.compile(
            r'^##\s+' + re.escape(titulo) + r'\s*\n(.*?)(?=\n##\s|\n---|\Z)',
            re.MULTILINE | re.DOTALL
        )
        m = patron.search(texto)
        return m.group(1).strip() if m else None

    @staticmethod
    def _extraer_bullets(bloque):
        items = []
        for linea in bloque.splitlines():
            linea = linea.strip()
            if linea.startswith("- "):
                valor = linea[2:].strip()
                if valor and valor != "-":
                    items.append(valor)
        return items
