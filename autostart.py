"""
CONFIGURAR ARRANQUE AUTOMÁTICO CON WINDOWS
==========================================
Corre este script UNA VEZ para que el asistente
inicie automáticamente cada vez que prendas el PC.

Uso:
  python autostart.py instalar   → activa el arranque automático
  python autostart.py desinstalar → desactiva el arranque automático
"""

import sys
import os
import winreg
from pathlib import Path

NOMBRE = "AsistenteVozClaude"

def get_paths():
    script_dir    = Path(__file__).parent.resolve()
    asistente_py  = script_dir / "asistente.py"
    python_exe    = sys.executable
    return python_exe, asistente_py

def instalar():
    python_exe, asistente_py = get_paths()

    if not asistente_py.exists():
        print(f"❌ No encontré asistente.py en {asistente_py}")
        sys.exit(1)

    # Comando que se ejecuta al iniciar Windows
    # Usa pythonw.exe para que NO abra ventana de terminal
    pythonw = str(Path(python_exe).parent / "pythonw.exe")
    if not Path(pythonw).exists():
        pythonw = python_exe  # fallback a python.exe si no hay pythonw

    comando = f'"{pythonw}" "{asistente_py}"'

    # Escribir en el registro de Windows (HKCU = solo este usuario)
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, NOMBRE, 0, winreg.REG_SZ, comando)
    winreg.CloseKey(key)

    print(f"✅ Arranque automático activado!")
    print(f"   Comando: {comando}")
    print(f"\nLa próxima vez que enciendas el PC, el asistente")
    print(f"iniciará automáticamente en segundo plano.")
    print(f"\nNota: La primera vez tarda ~10 segundos en estar listo.")

def desinstalar():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, NOMBRE)
        winreg.CloseKey(key)
        print("✅ Arranque automático desactivado.")
    except FileNotFoundError:
        print("ℹ️  El arranque automático no estaba activado.")

def verificar():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, NOMBRE)
        winreg.CloseKey(key)
        print(f"✅ Arranque automático ACTIVO")
        print(f"   Comando: {val}")
    except FileNotFoundError:
        print("❌ Arranque automático NO está activo")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nEjemplos:")
        print("  python autostart.py instalar")
        print("  python autostart.py desinstalar")
        print("  python autostart.py verificar")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "instalar":
        instalar()
    elif cmd == "desinstalar":
        desinstalar()
    elif cmd == "verificar":
        verificar()
    else:
        print(f"Comando no reconocido: {cmd}")
        print("Usa: instalar | desinstalar | verificar")
