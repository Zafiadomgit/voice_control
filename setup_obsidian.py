"""
CONFIGURAR EL VAULT DE OBSIDIAN PARA ALFRED
=============================================
Corre este script UNA VEZ para crear la estructura del vault donde
Alfred va a guardar su memoria (nombre, preferencias, notas, resumen
de conversaciones, notas diarias).

Uso:
  python setup_obsidian.py                          → usa OBSIDIAN_VAULT_PATH de .env
  python setup_obsidian.py "C:\\Users\\david\\Documents\\Vault"  → ruta explícita

Después de correrlo:
  1. Abre esa carpeta como vault en la app de Obsidian (https://obsidian.md).
  2. Añade OBSIDIAN_VAULT_PATH=<ruta> a tu .env si no lo tenías.
  3. Pídele a Alfred o a Claude Code "entrevístame y completa mi VAULT-INDEX"
     para rellenar tu perfil.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PLANTILLAS = SCRIPT_DIR / "vault_templates"

CARPETAS = [
    "00 - Bandeja de Entrada",
    "01 - Notas Diarias",
    "02 - Personal",
    "03 - Archivo",
    "04 - Recursos",
]


def cargar_ruta_desde_env():
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("OBSIDIAN_VAULT_PATH="):
            return line.split("=", 1)[1].strip()
    return None


def crear_vault(ruta_vault):
    ruta_vault = Path(ruta_vault)
    ruta_vault.mkdir(parents=True, exist_ok=True)
    print(f"📁 Vault en: {ruta_vault}")

    for carpeta in CARPETAS:
        (ruta_vault / carpeta).mkdir(exist_ok=True)
    print(f"✅ {len(CARPETAS)} carpetas creadas/verificadas.")

    destino_index = ruta_vault / "VAULT-INDEX.md"
    if not destino_index.exists():
        destino_index.write_text(
            (PLANTILLAS / "VAULT-INDEX.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        print("✅ VAULT-INDEX.md creado (con marcadores [RELLENAR] pendientes).")
    else:
        print("ℹ️  VAULT-INDEX.md ya existe, no lo toco.")

    destino_plantilla_diaria = ruta_vault / "01 - Notas Diarias" / "Plantilla Nota Diaria.md"
    if not destino_plantilla_diaria.exists():
        destino_plantilla_diaria.write_text(
            (PLANTILLAS / "DAILY-NOTE.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        print("✅ Plantilla Nota Diaria.md creada.")
    else:
        print("ℹ️  Plantilla Nota Diaria.md ya existe, no la toco.")

    destino_memoria = ruta_vault / "04 - Recursos" / "Memoria Alfred.md"
    if not destino_memoria.exists():
        destino_memoria.write_text(
            "---\nstatus: active\nproject: personal\ntype: reference\n---\n\n"
            "# Memoria de Alfred\n\n"
            "<!-- Mantenida automáticamente por asistente.py. No la edites a mano mientras Alfred está corriendo. -->\n\n"
            "## Nombre\n[RELLENAR: aún no me lo has dicho]\n\n"
            "## Preferencias\n-\n\n"
            "## Notas\n-\n\n"
            "## Resumen de Conversaciones Anteriores\n-\n",
            encoding="utf-8",
        )
        print("✅ Memoria Alfred.md creada.")
    else:
        print("ℹ️  Memoria Alfred.md ya existe, no la toco.")

    destino_prioridades = ruta_vault / "Prioridades Activas.md"
    if not destino_prioridades.exists():
        destino_prioridades.write_text(
            "---\nstatus: active\nproject: personal\ntype: plan\n---\n\n"
            "# Prioridades Activas\n\n"
            "Todo el trabajo abierto ahora mismo, en una sola lista.\n\n"
            "- [ ] \n",
            encoding="utf-8",
        )
        print("✅ Prioridades Activas.md creada.")
    else:
        print("ℹ️  Prioridades Activas.md ya existe, no la toco.")

    print("\n📝 Copia también el contenido de vault_templates/MEMORY.md dentro de tu carpeta")
    print("   de proyecto de Claude Code (ls ~/.claude/projects/ para encontrarla) si quieres")
    print("   que Claude Code redirija su memoria nativa hacia este vault.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        ruta = cargar_ruta_desde_env()
        if not ruta:
            print("❌ No encontré OBSIDIAN_VAULT_PATH en .env ni una ruta como argumento.")
            print('   Uso: python setup_obsidian.py "C:\\ruta\\a\\tu\\vault"')
            sys.exit(1)

    crear_vault(ruta)
    print("\n✅ Listo! Abre esa carpeta en la app de Obsidian y arranca Alfred.")
