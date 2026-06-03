"""
ALFRED - VOICE ASSISTANT
========================
- Edge TTS voice (es-ES-AlvaroNeural, gratis e ilimitado)
- Wake word: "Alfred"
- Background browser (Playwright) + DuckDuckGo search
- Program control + PC control (shutdown, restart, volume, brightness)
- Claude Code integration via voice
- Google STT (español)
- Memoria persistente (nombre, preferencias)
- Python 3.10+ Windows

.env file:
  ANTHROPIC_API_KEY=sk-ant-...
"""

import os, sys, json, subprocess, tempfile, time, threading, base64, asyncio
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav_io
import anthropic
from pathlib import Path
from playsound3 import playsound
from datetime import datetime, timedelta

WAKE_WORD      = "alfred"
EDGE_TTS_VOICE = "es-MX-JorgeNeural"
OPERA_PATH     = r"C:\Users\david\AppData\Local\Programs\Opera GX\opera.exe"
MEMORIA_PATH     = Path(__file__).parent / "memoria.json"

# ─────────────────────────────────────────
# ENV
# ─────────────────────────────────────────

def cargar_env():
    keys = {}
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in open(env_path):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip()
    for k in ["ANTHROPIC_API_KEY"]:
        if k not in keys and os.environ.get(k):
            keys[k] = os.environ[k]
    return keys

# ─────────────────────────────────────────
# MEMORIA
# ─────────────────────────────────────────

def cargar_memoria():
    if MEMORIA_PATH.exists():
        try:
            return json.loads(MEMORIA_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {"nombre": None, "preferencias": [], "notas": [], "programas": {}}

def guardar_memoria(mem):
    MEMORIA_PATH.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

def memoria_a_texto(mem):
    partes = []
    if mem.get("nombre"):
        partes.append(f"El nombre del usuario es {mem['nombre']}.")
    if mem.get("preferencias"):
        partes.append("Preferencias del usuario: " + "; ".join(mem["preferencias"]) + ".")
    if mem.get("notas"):
        partes.append("Notas guardadas: " + "; ".join(mem["notas"]) + ".")
    if mem.get("resumen_conversacion"):
        partes.append("Resumen de conversaciones anteriores: " + mem["resumen_conversacion"])
    return "\n".join(partes) if partes else ""

# ─────────────────────────────────────────
# PROGRAMS
# ─────────────────────────────────────────

PROGRAMAS = {
    "lol":               [r"C:\Riot Games\League of Legends\LeagueClient.exe", r"D:\Riot Games\League of Legends\LeagueClient.exe"],
    "league":            [r"C:\Riot Games\League of Legends\LeagueClient.exe", r"D:\Riot Games\League of Legends\LeagueClient.exe"],
    "league of legends": [r"C:\Riot Games\League of Legends\LeagueClient.exe", r"D:\Riot Games\League of Legends\LeagueClient.exe"],
    "valorant":          [r"C:\Riot Games\VALORANT\live\VALORANT.exe", r"D:\Riot Games\VALORANT\live\VALORANT.exe"],
    "steam":             [r"C:\Program Files (x86)\Steam\steam.exe", r"C:\Program Files\Steam\steam.exe"],
    "epic games":        [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"],
    "epic":              [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"],
    "ankama":            [r"%LOCALAPPDATA%\Ankama\ankama_launcher\ankama_launcher.exe", r"C:\Program Files (x86)\Ankama\Ankama Launcher\Ankama Launcher.exe", r"%LOCALAPPDATA%\Ankama\Ankama Launcher\Ankama Launcher.exe"],
    "ankama launcher":   [r"%LOCALAPPDATA%\Ankama\ankama_launcher\ankama_launcher.exe", r"C:\Program Files (x86)\Ankama\Ankama Launcher\Ankama Launcher.exe", r"%LOCALAPPDATA%\Ankama\Ankama Launcher\Ankama Launcher.exe"],
    "dofus":             [r"%LOCALAPPDATA%\Ankama\ankama_launcher\ankama_launcher.exe"],
    "wakfu":             [r"%LOCALAPPDATA%\Ankama\ankama_launcher\ankama_launcher.exe"],
    "opera":             [OPERA_PATH],
    "opera gx":          [OPERA_PATH],
    "browser":           [OPERA_PATH],
    "navegador":         [OPERA_PATH],
    "chrome":            [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox":           [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "edge":              [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "vscode":            [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "vs code":           [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "visual studio":     [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"],
    "discord":           [r"%LOCALAPPDATA%\Discord\app-*\Discord.exe"],
    "spotify":           [r"%APPDATA%\Spotify\Spotify.exe"],
    "whatsapp":          [r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"],
    "notepad":           ["notepad.exe"],
    "bloc de notas":     ["notepad.exe"],
    "calculator":        ["calc.exe"],
    "calculadora":       ["calc.exe"],
    "explorer":          ["explorer.exe"],
    "explorador":        ["explorer.exe"],
    "task manager":      ["taskmgr.exe"],
    "administrador de tareas": ["taskmgr.exe"],
    "claude":            [r"%LOCALAPPDATA%\Programs\claude\Claude.exe"],
    "claude code":       ["cmd.exe"],
}

# ─────────────────────────────────────────
# VOICE
# ─────────────────────────────────────────

class Voz:
    def __init__(self, api_key=None):
        self._hablando = False

    def interrumpir(self):
        try:
            sd.stop()
        except:
            pass
        self._hablando = False

    def hablar(self, texto):
        print(f"\n🔊 Alfred: {texto}\n")
        self._hablando = True
        tmp = None
        try:
            import edge_tts, soundfile as sf
            tmp = tempfile.mktemp(suffix=".mp3")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._run_tts_sync, texto, tmp)
                future.result()
            data, samplerate = sf.read(tmp, dtype='float32')
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            print(f"[ERROR VOICE] {e}")
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(texto)
                engine.runAndWait()
                engine.stop()
            except:
                pass
        finally:
            self._hablando = False
            if tmp:
                try:
                    time.sleep(0.1)
                    os.unlink(tmp)
                except:
                    pass

    def _run_tts_sync(self, texto, ruta):
        import edge_tts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            communicator = edge_tts.Communicate(texto, EDGE_TTS_VOICE)
            loop.run_until_complete(communicator.save(ruta))
        finally:
            loop.close()

# ─────────────────────────────────────────
# MICROPHONE — Google STT, modo standby vs activo
# ─────────────────────────────────────────

class Microfono:
    def __init__(self):
        self.sample_rate = 16000
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        print("🎙️  Google STT listo (español)")

    def grabar(self, max_segundos=8, silencio_segundos=1.2, timeout_sin_voz=2.5):
        chunk = int(self.sample_rate * 0.03)
        chunks_sil     = int(silencio_segundos / 0.03)
        chunks_max     = int(max_segundos / 0.03)
        chunks_sin_voz = int(timeout_sin_voz / 0.03)
        grabando, silencio, hablo, sin_voz = [], 0, False, 0
        vol_max = 0.0
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
            for _ in range(chunks_max):
                data, _ = stream.read(chunk)
                grabando.append(data.copy())
                vol = float(np.abs(data).mean())
                if vol > vol_max:
                    vol_max = vol
                if vol > 0.003:
                    hablo = True
                    silencio = 0
                    sin_voz = 0
                elif hablo:
                    silencio += 1
                    if silencio >= chunks_sil:
                        break
                else:
                    sin_voz += 1
                    if sin_voz >= chunks_sin_voz:
                        break
        print(f"[MIC] vol_max={vol_max:.5f} hablo={hablo} muestras={len(grabando)}")
        return (np.concatenate(grabando) * 32767).astype(np.int16)

    def escuchar(self, modo_standby=False):
        try:
            if modo_standby:
                data = self.grabar(max_segundos=6, silencio_segundos=1.0, timeout_sin_voz=2.5)
            else:
                data = self.grabar(max_segundos=12, silencio_segundos=2.0, timeout_sin_voz=3.0)

            if len(data) < 800:
                return None

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                path = f.name
            wav_io.write(path, self.sample_rate, data)

            import speech_recognition as sr
            with sr.AudioFile(path) as src:
                audio = self.recognizer.record(src)
            os.unlink(path)

            try:
                return self.recognizer.recognize_google(audio, language="es-ES").lower().strip()
            except sr.UnknownValueError:
                return None
            except Exception as e:
                print(f"[STT ERROR] {e}")
                return None
        except Exception as e:
            print(f"[STT ERROR] {e}")
            return None

# ─────────────────────────────────────────
# BROWSER — DuckDuckGo search, Opera GX focus
# ─────────────────────────────────────────

class Navegador:
    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw     = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page    = self.context.new_page()
        self._last_search_url = None
        print("🌐 Navegador en segundo plano listo")

    def mostrar(self):
        url = self._last_search_url or "https://duckduckgo.com"
        try:
            # Abrir Opera GX con la URL
            if os.path.exists(OPERA_PATH):
                subprocess.Popen([OPERA_PATH, url])
            else:
                os.startfile(url)

            # Traer Opera GX al primer plano después de un momento
            time.sleep(1.5)
            self._enfocar_ventana("Opera")
            return url
        except Exception as e:
            print(f"[ERROR SHOW] {e}")
            return None

    def _enfocar_ventana(self, nombre_parcial):
        try:
            import win32gui, win32con
            def callback(hwnd, resultados):
                if win32gui.IsWindowVisible(hwnd):
                    titulo = win32gui.GetWindowText(hwnd)
                    if nombre_parcial.lower() in titulo.lower():
                        resultados.append(hwnd)
            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            if hwnds:
                hwnd = hwnds[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[FOCUS ERROR] {e}")

    def buscar(self, query):
        try:
            import urllib.request, urllib.parse, re
            q = urllib.parse.quote(query)
            self._last_search_url = f"https://duckduckgo.com/?q={q}"

            req = urllib.request.Request(
                f"https://html.duckduckgo.com/html/?q={q}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # extraer títulos y URLs del primer resultado
            titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if t.strip()]
            titles = [t for t in titles if len(t) > 5][:3]

            # navegar el browser headless al primer resultado para poder leer detalles
            urls = re.findall(r'class="result__url"[^>]*>(.*?)<', html)
            if urls:
                primer_url = urls[0].strip()
                if not primer_url.startswith("http"):
                    primer_url = "https://" + primer_url
                try:
                    self.page.goto(primer_url, wait_until="domcontentloaded", timeout=10000)
                    self._last_search_url = primer_url
                except:
                    pass

            return titles
        except Exception as e:
            print(f"[ERROR SEARCH] {e}")
            return []

    def leer_pagina(self):
        try:
            return self.page.evaluate("""() => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script,style,nav,footer,header,aside').forEach(e=>e.remove());
                return clone.innerText.substring(0,3000);
            }""")
        except:
            return ""

    def navegar(self, url):
        try:
            if not url.startswith("http"):
                url = "https://" + url
            self._last_search_url = url
            self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            self.page.wait_for_timeout(1500)
            return self.page.title()
        except Exception as e:
            print(f"[ERROR NAV] {e}")
            return url

    def cerrar(self):
        try:
            self.browser.close()
            self._pw.stop()
        except:
            pass

# ─────────────────────────────────────────
# PC CONTROL
# ─────────────────────────────────────────

class ControlPC:
    def abrir(self, nombre):
        n = nombre.lower().strip()
        if "claude code" in n:
            return self._abrir_claude_code()

        # Primero buscar en programas guardados por el usuario
        programas_guardados = getattr(self, 'programas_extra', {})
        for k, ruta in programas_guardados.items():
            if k in n or n in k:
                if self._ejecutar(ruta):
                    return True

        # Buscar en lista de programas conocidos
        for k, rutas in PROGRAMAS.items():
            if k in n or n in k:
                for ruta_template in rutas:
                    # Soporte para wildcards (ej. Discord app-*)
                    ruta = os.path.expandvars(ruta_template)
                    if "*" in ruta:
                        import glob
                        matches = glob.glob(ruta)
                        if matches:
                            ruta = matches[-1]  # versión más reciente
                        else:
                            continue
                    if os.path.exists(ruta) or not os.path.isabs(ruta):
                        if self._ejecutar(ruta):
                            return True

        # Buscar en el registro de Windows (programas instalados)
        ruta_reg = self._buscar_en_registro(n)
        if ruta_reg and self._ejecutar(ruta_reg):
            return True

        # Último recurso: buscar en PATH del sistema (silenciosamente)
        try:
            resultado = subprocess.run(["where", n.split()[0]], capture_output=True, text=True)
            if resultado.returncode == 0:
                exe = resultado.stdout.strip().split("\n")[0]
                subprocess.Popen(exe, shell=True)
                return True
        except:
            pass
        return False

    def _ejecutar(self, ruta):
        try:
            subprocess.Popen(ruta, shell=True)
            return True
        except:
            return False

    def _buscar_en_registro(self, nombre):
        try:
            import winreg
            claves = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]
            for clave_base in claves:
                try:
                    reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clave_base)
                    for i in range(winreg.QueryInfoKey(reg)[0]):
                        try:
                            sub = winreg.OpenKey(reg, winreg.EnumKey(reg, i))
                            display = winreg.QueryValueEx(sub, "DisplayName")[0].lower()
                            if nombre in display or display in nombre:
                                loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
                                if loc:
                                    # buscar .exe en esa carpeta
                                    for f in os.listdir(loc):
                                        if f.lower().endswith(".exe") and nombre.split()[0] in f.lower():
                                            return os.path.join(loc, f)
                        except:
                            continue
                except:
                    continue
        except:
            pass
        return None

    def _abrir_claude_code(self, prompt=None):
        try:
            cmd = f'start cmd /k claude' + (f' "{prompt}"' if prompt else '')
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            print(f"[ERROR CLAUDE CODE] {e}")
            return False

    def claude_code_con_prompt(self, prompt):
        return self._abrir_claude_code(prompt=prompt)

    def apagar(self, reiniciar=False):
        try:
            subprocess.Popen(f"shutdown /{'r' if reiniciar else 's'} /t 10", shell=True)
            return True
        except Exception as e:
            print(f"[ERROR SHUTDOWN] {e}")
            return False

    def cancelar_apagado(self):
        try:
            subprocess.Popen("shutdown /a", shell=True)
            return True
        except:
            return False

    def volumen(self, accion, cantidad=10):
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            if accion == "silenciar":
                volume.SetMute(1, None)
            elif accion == "activar":
                volume.SetMute(0, None)
            elif accion in ("subir", "bajar"):
                current = volume.GetMasterVolumeLevelScalar()
                delta = cantidad / 100.0
                new_vol = min(1.0, current + delta) if accion == "subir" else max(0.0, current - delta)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
            return True
        except Exception as e:
            print(f"[ERROR VOLUME] {e}")
            return False

    def brillo(self, accion, cantidad=10):
        try:
            import wmi
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            current = c.WmiMonitorBrightness()[0].CurrentBrightness
            if accion == "subir":
                new_val = min(100, current + cantidad)
            elif accion == "bajar":
                new_val = max(0, current - cantidad)
            else:
                new_val = max(0, min(100, cantidad))
            methods.WmiSetBrightness(new_val, 0)
            return True
        except Exception as e:
            print(f"[ERROR BRIGHTNESS] {e}")
            return False

# ─────────────────────────────────────────
# MOUSE / KEYBOARD CONTROL  (Feature 3)
# ─────────────────────────────────────────

class ControlMouse:
    def click(self, x, y):
        try:
            import pyautogui
            pyautogui.click(x, y)
            return True
        except Exception as e:
            print(f"[ERROR CLICK] {e}")
            return False

    def escribir(self, texto):
        try:
            import pyautogui
            pyautogui.typewrite(texto, interval=0.05)
            return True
        except Exception as e:
            print(f"[ERROR ESCRIBIR] {e}")
            return False

    def hotkey(self, *keys):
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            print(f"[ERROR HOTKEY] {e}")
            return False

    def mover(self, x, y):
        try:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0.3)
            return True
        except Exception as e:
            print(f"[ERROR MOVER] {e}")
            return False

    def screenshot_y_analizar(self, pregunta, cerebro):
        try:
            import pyautogui
            from PIL import Image
            import io
            screenshot = pyautogui.screenshot()
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            r = cerebro.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64,
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Responde en español, máximo 3 oraciones. {pregunta}"
                        }
                    ]
                }]
            )
            return r.content[0].text.strip()
        except Exception as e:
            print(f"[ERROR SCREENSHOT] {e}")
            return "No pude analizar la pantalla."

# ─────────────────────────────────────────
# BRAIN
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# RECORDATORIOS
# ─────────────────────────────────────────

class GestorRecordatorios:
    def __init__(self, voz):
        self.voz = voz
        self.recordatorios = []
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def agregar(self, mensaje, segundos):
        cuando = datetime.now() + timedelta(seconds=segundos)
        self.recordatorios.append({"mensaje": mensaje, "cuando": cuando})
        print(f"[RECORDATORIO] Programado: '{mensaje}' en {segundos}s")

    def _loop(self):
        while True:
            ahora = datetime.now()
            pendientes = []
            for r in self.recordatorios:
                if ahora >= r["cuando"]:
                    self.voz.hablar(f"Recordatorio: {r['mensaje']}")
                else:
                    pendientes.append(r)
            self.recordatorios = pendientes
            time.sleep(5)

# ─────────────────────────────────────────
# MONITOR DEL SISTEMA
# ─────────────────────────────────────────

class MonitorSistema:
    def __init__(self, voz):
        self.voz = voz
        self.inicio_sesion = datetime.now()
        self._alertas = {"cpu": False, "ram": False, "disco": False, "tiempo": False}
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def _loop(self):
        while True:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=2)
                ram = psutil.virtual_memory().percent
                disco = psutil.disk_usage('/').percent

                if cpu > 90 and not self._alertas["cpu"]:
                    self._alertas["cpu"] = True
                    self.voz.hablar(f"Alerta: el CPU está al {int(cpu)} porciento.")
                elif cpu < 70:
                    self._alertas["cpu"] = False

                if ram > 90 and not self._alertas["ram"]:
                    self._alertas["ram"] = True
                    self.voz.hablar(f"Alerta: la memoria RAM está al {int(ram)} porciento.")
                elif ram < 80:
                    self._alertas["ram"] = False

                if disco > 95 and not self._alertas["disco"]:
                    self._alertas["disco"] = True
                    self.voz.hablar("Alerta: el disco duro está casi lleno.")

                # Alerta por tiempo frente al PC cada 2 horas
                minutos = (datetime.now() - self.inicio_sesion).seconds // 60
                if minutos > 0 and minutos % 120 == 0 and not self._alertas["tiempo"]:
                    self._alertas["tiempo"] = True
                    horas = minutos // 60
                    self.voz.hablar(f"Llevas {horas} hora{'s' if horas>1 else ''} frente al PC. Considera tomar un descanso.")
                elif minutos % 120 != 0:
                    self._alertas["tiempo"] = False

            except ImportError:
                pass
            except Exception as e:
                print(f"[MONITOR] {e}")
            time.sleep(30)

    def estado(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disco = psutil.disk_usage('/').percent
            minutos = (datetime.now() - self.inicio_sesion).seconds // 60
            return f"CPU al {int(cpu)}%, RAM al {int(ram)}%, disco al {int(disco)}%, llevas {minutos} minutos en sesión."
        except:
            return "No puedo leer el estado del sistema."

# ─────────────────────────────────────────
# GESTIÓN DE VENTANAS
# ─────────────────────────────────────────

class GestorVentanas:
    def _ventanas(self, nombre=None):
        try:
            import win32gui, win32con
            resultado = []
            def cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    t = win32gui.GetWindowText(hwnd)
                    if t and (nombre is None or nombre.lower() in t.lower()):
                        resultado.append((hwnd, t))
            win32gui.EnumWindows(cb, None)
            return resultado
        except:
            return []

    def enfocar(self, nombre):
        import win32gui, win32con
        for hwnd, titulo in self._ventanas(nombre):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return f"Enfocando {titulo}."
        return f"No encontré ventana con '{nombre}'."

    def maximizar(self, nombre):
        import win32gui, win32con
        for hwnd, titulo in self._ventanas(nombre):
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return f"Maximizando {titulo}."
        return f"No encontré '{nombre}'."

    def minimizar(self, nombre):
        import win32gui, win32con
        for hwnd, titulo in self._ventanas(nombre):
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return f"Minimizando {titulo}."
        return f"No encontré '{nombre}'."

    def cerrar(self, nombre):
        import win32gui, win32con
        for hwnd, titulo in self._ventanas(nombre):
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return f"Cerrando {titulo}."
        return f"No encontré '{nombre}'."

    def listar(self):
        ventanas = self._ventanas()
        nombres = [t for _, t in ventanas[:8]]
        return "Ventanas abiertas: " + ", ".join(nombres) if nombres else "No hay ventanas abiertas."

# ─────────────────────────────────────────
# BÚSQUEDA DE ARCHIVOS
# ─────────────────────────────────────────

class BuscadorArchivos:
    CARPETAS = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/OneDrive"),
        os.path.expanduser("~/OneDrive/Escritorio"),
        os.path.expanduser("~/OneDrive/Documentos"),
    ]

    def buscar(self, nombre, max_resultados=5):
        resultados = []
        try:
            for carpeta in self.CARPETAS:
                if not os.path.exists(carpeta):
                    continue
                for root, dirs, files in os.walk(carpeta):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in files:
                        if nombre.lower() in f.lower():
                            resultados.append(os.path.join(root, f))
                            if len(resultados) >= max_resultados:
                                return resultados
        except Exception as e:
            print(f"[BUSCAR ARCHIVOS] {e}")
        return resultados

    def abrir(self, ruta):
        try:
            os.startfile(ruta)
            return True
        except:
            return False

# ─────────────────────────────────────────
# WHATSAPP WEB
# ─────────────────────────────────────────

class WhatsAppWeb:
    def __init__(self, navegador_playwright):
        self._nav = navegador_playwright
        self._listo = False

    def abrir(self):
        try:
            self._nav.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=20000)
            self._nav.page.wait_for_timeout(5000)
            self._listo = True
            return True
        except:
            return False

    def enviar(self, contacto, mensaje):
        try:
            page = self._nav.page
            if "web.whatsapp.com" not in page.url:
                self.abrir()
            # Buscar contacto
            page.click('[data-icon="search"]')
            page.wait_for_timeout(500)
            page.keyboard.type(contacto)
            page.wait_for_timeout(2000)
            # Click primer resultado
            resultados = page.query_selector_all('[data-testid="cell-frame-container"]')
            if not resultados:
                return False
            resultados[0].click()
            page.wait_for_timeout(1000)
            # Escribir y enviar
            caja = page.query_selector('[data-testid="conversation-compose-box-input"]')
            if not caja:
                return False
            caja.click()
            caja.type(mensaje)
            page.keyboard.press("Enter")
            return True
        except Exception as e:
            print(f"[WHATSAPP] {e}")
            return False

# ─────────────────────────────────────────
# APRENDIZAJE DE HÁBITOS
# ─────────────────────────────────────────

class AprendizajeHabitos:
    def __init__(self, memoria, voz):
        self.memoria = memoria
        self.voz = voz
        if "habitos" not in self.memoria:
            self.memoria["habitos"] = {}
        if "sugerencias_dadas" not in self.memoria:
            self.memoria["sugerencias_dadas"] = {}

    def registrar(self, accion, valor):
        hora = datetime.now().strftime("%H")
        clave = f"{hora}:{accion}:{valor}"
        habitos = self.memoria["habitos"]
        habitos[clave] = habitos.get(clave, 0) + 1
        # Si se repite 3+ veces, sugerir
        if habitos[clave] == 3:
            return self._sugerir(accion, valor, hora)
        return None

    def _sugerir(self, accion, valor, hora):
        ya_sugerido = self.memoria["sugerencias_dadas"].get(f"{hora}:{accion}:{valor}", 0)
        if ya_sugerido > 0:
            return None
        self.memoria["sugerencias_dadas"][f"{hora}:{accion}:{valor}"] = 1
        if accion == "abrir_programa":
            return f"Noto que siempre abres {valor} a esta hora. ¿Quieres que lo abra automáticamente?"
        return None


SYSTEM_PROMPT_BASE = """Eres Alfred, un asistente de voz personal masculino que controla un PC con Windows.
Respondes siempre en español, con naturalidad y brevedad. Hablas como un mayordomo inteligente y eficiente.

{memoria}

Puedes hacer:
1. Abrir programas: LOL, Steam, Opera GX, Discord, Spotify, VSCode, Chrome, WhatsApp, Claude, Claude Code, etc.
2. Buscar en la web y reportar resultados
3. Navegar a sitios web
4. Controlar el PC: apagar, reiniciar, volumen, brillo
5. Abrir Claude Code con un prompt de voz
6. Recordar información del usuario (nombre, preferencias, notas)
7. Conversación natural
8. Ejecutar planes multi-paso para tareas complejas
9. Controlar el ratón y teclado del PC
10. Tomar capturas de pantalla y describir lo que hay en pantalla
11. Poner recordatorios por voz ("avísame en 30 minutos que tengo reunión")
12. Ver estado del sistema (CPU, RAM, disco, tiempo en sesión)
13. Gestionar ventanas: maximizar, minimizar, cerrar, enfocar por nombre
14. Buscar archivos en el PC por nombre
15. Enviar mensajes de WhatsApp por voz
16. Listar ventanas abiertas

RESPONDE SOLO EN JSON PURO, SIN MARKDOWN, SIN EXPLICACIÓN:
{"accion":"abrir_programa"|"buscar_web"|"navegar_url"|"mostrar_navegador"|"leer_pagina"|"apagar_pc"|"reiniciar_pc"|"cancelar_apagado"|"volumen"|"brillo"|"claude_code"|"guardar_memoria"|"guardar_programa"|"mouse_click"|"escribir_texto"|"hotkey"|"screenshot"|"plan"|"recordatorio"|"estado_sistema"|"ventana"|"buscar_archivo"|"whatsapp"|"responder",
 "programa":"nombre o null",
 "query":"búsqueda o null",
 "url":"url o null",
 "subaccion":"subir"|"bajar"|"silenciar"|"activar"|"establecer" o null,
 "cantidad":número o null,
 "prompt_claude":"tarea para claude code o null",
 "memoria_key":"nombre"|"preferencia"|"nota" o null,
 "memoria_valor":"valor a guardar o null",
 "prog_nombre":"nombre del programa a guardar o null",
 "prog_ruta":"ruta del ejecutable o null",
 "mouse_x":número o null,
 "mouse_y":número o null,
 "texto_escribir":"texto a escribir o null",
 "teclas":"combinación de teclas ej. ctrl+c o null",
 "pasos":["lista","de","pasos"] o null,
 "recordatorio_msg":"texto del recordatorio o null",
 "recordatorio_seg":segundos o null,
 "ventana_accion":"enfocar"|"maximizar"|"minimizar"|"cerrar"|"listar" o null,
 "ventana_nombre":"nombre parcial de la ventana o null",
 "archivo_buscar":"nombre del archivo o null",
 "wa_contacto":"nombre del contacto de whatsapp o null",
 "wa_mensaje":"mensaje a enviar o null",
 "mensaje":"respuesta en español, máximo 2 oraciones"}

RECORDATORIOS:
"avísame en 30 minutos" -> {"accion":"recordatorio","recordatorio_msg":"Recordatorio","recordatorio_seg":1800,"mensaje":"Listo, te aviso en 30 minutos."}
"recuérdame tomar agua en 1 hora" -> {"accion":"recordatorio","recordatorio_msg":"tomar agua","recordatorio_seg":3600,"mensaje":"Anotado, te aviso en una hora."}

VENTANAS:
"maximiza el discord" -> {"accion":"ventana","ventana_accion":"maximizar","ventana_nombre":"discord","mensaje":"Maximizando Discord."}
"cierra el spotify" -> {"accion":"ventana","ventana_accion":"cerrar","ventana_nombre":"spotify","mensaje":"Cerrando Spotify."}
"qué ventanas tengo abiertas" -> {"accion":"ventana","ventana_accion":"listar","ventana_nombre":null,"mensaje":"Revisando ventanas abiertas."}

ARCHIVOS:
"busca el archivo contrato" -> {"accion":"buscar_archivo","archivo_buscar":"contrato","mensaje":"Buscando en tus carpetas."}

WHATSAPP:
"manda un whatsapp a mamá que llego tarde" -> {"accion":"whatsapp","wa_contacto":"mamá","wa_mensaje":"Llego tarde","mensaje":"Enviando mensaje a mamá por WhatsApp."}

ESTADO SISTEMA:
"cómo está el sistema" -> {"accion":"estado_sistema","mensaje":"Revisando el estado del sistema."}

PLANES — cuando una tarea requiere múltiples acciones encadenadas, usa accion "plan":
Ejemplo: "busca vuelos a Brasil y dime el más barato"
-> {"accion":"plan","pasos":["buscar_web:vuelos baratos a Brasil","leer_pagina","responder"],"mensaje":"Voy a buscar y analizar los vuelos, dame un momento."}
Los pasos pueden ser: "buscar_web:<query>", "leer_pagina", "navegar_url:<url>", "responder"

CONTROL DE RATÓN Y TECLADO:
"haz clic en x=500 y=300" -> {"accion":"mouse_click","mouse_x":500,"mouse_y":300,"mensaje":"Haciendo clic."}
"escribe hola mundo" -> {"accion":"escribir_texto","texto_escribir":"hola mundo","mensaje":"Escribiendo el texto."}
"presiona ctrl+c" -> {"accion":"hotkey","teclas":"ctrl+c","mensaje":"Copiando al portapapeles."}
"qué hay en pantalla" -> {"accion":"screenshot","mensaje":"Analizando la pantalla."}

GUARDAR MEMORIA — cuando el usuario diga su nombre, una preferencia o algo que quiera que recuerdes:
"me llamo David" -> {"accion":"guardar_memoria","memoria_key":"nombre","memoria_valor":"David","mensaje":"Perfecto, ya sé que te llamas David!"}
"prefiero resultados en español" -> {"accion":"guardar_memoria","memoria_key":"preferencia","memoria_valor":"prefiere resultados en español","mensaje":"Anotado, buscaré en español."}
"recuerda que trabajo de noche" -> {"accion":"guardar_memoria","memoria_key":"nota","memoria_valor":"trabaja de noche","mensaje":"Lo tengo en cuenta!"}"""

class Cerebro:
    def __init__(self, api_key, memoria):
        self.client    = anthropic.Anthropic(api_key=api_key)
        self.historial = []
        self.memoria   = memoria

    def system_prompt(self):
        mem_texto = memoria_a_texto(self.memoria)
        bloque = f"\nINFORMACIÓN DEL USUARIO:\n{mem_texto}" if mem_texto else ""
        return SYSTEM_PROMPT_BASE.replace("{memoria}", bloque)

    def resumir_pagina(self, contenido, pregunta):
        try:
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                system="Eres Alfred, asistente de voz masculino. Responde en español, máximo 3 oraciones, solo con la información relevante a la pregunta del usuario. Sin markdown.",
                messages=[{"role": "user", "content": f"Pregunta: {pregunta}\n\nContenido de la página:\n{contenido[:2000]}"}]
            )
            return r.content[0].text.strip()
        except Exception as e:
            print(f"[ERROR RESUMEN] {e}")
            return "No pude procesar el contenido de la página."

    def _comprimir_historial(self):
        """Summarize the oldest 10 messages into a single summary and save to memoria."""
        mensajes_a_resumir = self.historial[:10]
        self.historial = self.historial[10:]
        try:
            texto_conv = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in mensajes_a_resumir
            )
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                system="Resume la siguiente conversación en español en 2-3 oraciones, capturando los temas principales y decisiones tomadas. Sin markdown.",
                messages=[{"role": "user", "content": texto_conv}]
            )
            resumen = r.content[0].text.strip()
            resumen_anterior = self.memoria.get("resumen_conversacion", "")
            if resumen_anterior:
                self.memoria["resumen_conversacion"] = resumen_anterior + " " + resumen
            else:
                self.memoria["resumen_conversacion"] = resumen
            guardar_memoria(self.memoria)
            print(f"[MEMORIA] Historial comprimido. Resumen guardado.")
        except Exception as e:
            print(f"[ERROR COMPRIMIR] {e}")

    def procesar(self, texto):
        self.historial.append({"role": "user", "content": texto})
        if len(self.historial) >= 16:
            self._comprimir_historial()
        elif len(self.historial) > 20:
            self.historial = self.historial[-20:]
        try:
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                system=self.system_prompt(),
                messages=self.historial
            )
            raw = r.content[0].text.strip().replace("```json","").replace("```","").strip()
            print(f"[DEBUG] {raw}")
            self.historial.append({"role": "assistant", "content": raw})
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"accion":"responder","mensaje":"Un momento, tuve un problema procesando eso."}
        except Exception as e:
            print(f"[ERROR API] {e}")
            return {"accion":"responder","mensaje":"Problemas de conexión, intenta de nuevo."}

    def ejecutar_plan(self, pasos, contexto, navegador, cerebro_ref):
        """Execute a list of plan steps sequentially, passing results between steps."""
        resultado_anterior = contexto
        ultimo_mensaje = ""
        for paso in pasos:
            print(f"[PLAN] Ejecutando paso: {paso}")
            if paso.startswith("buscar_web:"):
                query = paso[len("buscar_web:"):]
                try:
                    resultados = navegador.buscar(query)
                    resultado_anterior = (
                        f"Resultados de búsqueda para '{query}': " + ". ".join(resultados[:3])
                        if resultados
                        else f"No se encontraron resultados para '{query}'."
                    )
                    ultimo_mensaje = resultado_anterior
                except Exception as e:
                    resultado_anterior = f"Error buscando: {e}"
            elif paso == "leer_pagina":
                contenido = navegador.leer_pagina()
                if contenido:
                    resumen = self.resumir_pagina(contenido, resultado_anterior)
                    resultado_anterior = resumen
                    ultimo_mensaje = resumen
                else:
                    resultado_anterior = "No se pudo leer la página."
            elif paso.startswith("navegar_url:"):
                url = paso[len("navegar_url:"):]
                try:
                    title = navegador.navegar(url)
                    resultado_anterior = f"Navegado a {title}."
                    ultimo_mensaje = resultado_anterior
                except Exception as e:
                    resultado_anterior = f"Error navegando: {e}"
            elif paso == "responder":
                # Ask Claude to formulate a final answer based on accumulated context
                try:
                    r = self.client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=200,
                        system="Eres Alfred, asistente de voz masculino. Responde en español, máximo 2 oraciones, de forma natural y directa. Sin markdown.",
                        messages=[{"role": "user", "content": f"Basándote en esta información, da una respuesta útil al usuario:\n{resultado_anterior}"}]
                    )
                    ultimo_mensaje = r.content[0].text.strip()
                    resultado_anterior = ultimo_mensaje
                except Exception as e:
                    print(f"[ERROR PLAN RESPONDER] {e}")
        return ultimo_mensaje or resultado_anterior

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print("\n" + "="*52)
    print("   🤖  Jade — Asistente de Voz  |  Windows")
    print("="*52 + "\n")

    keys = cargar_env()
    if "ANTHROPIC_API_KEY" not in keys:
        print("❌ Falta ANTHROPIC_API_KEY en .env"); sys.exit(1)
    memoria  = cargar_memoria()
    print(f"🧠 Memoria cargada: {memoria}")

    print("🔧 Iniciando...\n")
    voz        = Voz()
    mic        = Microfono()
    pc         = ControlPC()
    mouse      = ControlMouse()
    ventanas   = GestorVentanas()
    archivos   = BuscadorArchivos()
    habitos    = AprendizajeHabitos(memoria, voz)
    recordatorios = GestorRecordatorios(voz)
    monitor    = MonitorSistema(voz)
    pc.programas_extra = memoria.get("programas", {})
    cerebro    = Cerebro(keys["ANTHROPIC_API_KEY"], memoria)

    print("🌐 Iniciando navegador en segundo plano...")
    navegador  = Navegador()
    whatsapp   = WhatsAppWeb(navegador)

    nombre = memoria.get("nombre") or "usuario"
    print(f"\n✅ Listo! Di 'JADE' para activarme | Ctrl+C para salir\n")
    print("-"*52)

    hora = datetime.now().hour
    if memoria.get("nombre"):
        if 5 <= hora < 12:
            saludo = f"Buenos días {nombre}! Lista para ayudarte."
        elif 12 <= hora < 20:
            saludo = f"Buenas tardes {nombre}! Aquí estoy."
        else:
            saludo = f"Buenas noches {nombre}! En qué te ayudo."
    else:
        saludo = "Buenas. Soy Alfred, su asistente personal. Llámeme cuando me necesite."
    voz.hablar(saludo)

    modo_activo    = False
    turnos_activos = 0
    ultimo_texto   = 0
    WAKE_WORDS     = ["alfred", "alfredo", "alfred?"]

    hilo_voz = None

    while True:
        try:
            # Escuchar en hilo separado mientras Jade habla (para poder interrumpir)
            texto = mic.escuchar(modo_standby=not modo_activo)

            if not texto:
                if modo_activo and (time.time() - ultimo_texto > 45):
                    print("[timeout] Volviendo a standby")
                    modo_activo = False
                continue

            ultimo_texto = time.time()

            # Interrumpir a Jade si está hablando
            if voz._hablando:
                voz.interrumpir()
                time.sleep(0.3)

            print(f"👤 [{'ON' if modo_activo else 'standby'}] {texto}")

            # ── Standby: cualquier frase con "jade" activa ──
            if not modo_activo:
                if any(w in texto for w in WAKE_WORDS):
                    modo_activo    = True
                    turnos_activos = 0
                    comando = texto
                    for w in WAKE_WORDS:
                        comando = comando.replace(w, "").strip(" ,.")
                    if len(comando) > 3:
                        texto_procesar = comando
                    else:
                        voz.hablar("Dime!")
                        continue
                else:
                    continue
            else:
                texto_procesar = texto

            # ── Desactivar ──
            if any(p in texto for p in ["adiós","bye","gracias","para de escuchar","silencio","stop"]):
                voz.hablar("Listo, llámame cuando me necesites!")
                modo_activo = False
                continue

            resp             = cerebro.procesar(texto_procesar)
            accion           = resp.get("accion")
            programa         = resp.get("programa")
            query            = resp.get("query")
            url              = resp.get("url")
            subaccion        = resp.get("subaccion")
            cantidad         = resp.get("cantidad") or 10
            prompt_claude    = resp.get("prompt_claude")
            mem_key          = resp.get("memoria_key")
            mem_valor        = resp.get("memoria_valor")
            prog_nombre      = resp.get("prog_nombre")
            prog_ruta        = resp.get("prog_ruta")
            mouse_x          = resp.get("mouse_x")
            mouse_y          = resp.get("mouse_y")
            texto_escribir   = resp.get("texto_escribir")
            teclas           = resp.get("teclas")
            pasos            = resp.get("pasos")
            rec_msg          = resp.get("recordatorio_msg")
            rec_seg          = resp.get("recordatorio_seg")
            vent_accion      = resp.get("ventana_accion")
            vent_nombre      = resp.get("ventana_nombre") or ""
            archivo_buscar   = resp.get("archivo_buscar")
            wa_contacto      = resp.get("wa_contacto")
            wa_mensaje_txt   = resp.get("wa_mensaje")
            mensaje          = resp.get("mensaje", "Hecho!")

            # Registrar hábito
            if accion == "abrir_programa" and programa:
                sugerencia = habitos.registrar("abrir_programa", programa)
                if sugerencia:
                    guardar_memoria(cerebro.memoria)

            if accion == "abrir_programa" and programa:
                if not pc.abrir(programa):
                    mensaje = f"No encontré {programa}. Asegúrate de que esté instalado."

            elif accion == "buscar_web" and query:
                voz.hablar(mensaje)
                try:
                    resultados = navegador.buscar(query)
                    if resultados:
                        resumen = ". ".join(resultados[:2])
                        mensaje = f"Encontré esto: {resumen}. Di muéstrame para verlo en Opera GX."
                    else:
                        mensaje = "Busqué pero no encontré resultados. Di muéstrame para ver el navegador."
                except Exception as e:
                    print(f"[ERROR BROWSER] {e}")
                    mensaje = "Tuve un problema buscando, intenta de nuevo."

            elif accion == "navegar_url" and url:
                voz.hablar(mensaje)
                try:
                    title = navegador.navegar(url)
                    mensaje = f"Estoy en {title}. Di muéstrame si quieres verlo."
                except Exception as e:
                    mensaje = "Tuve un problema navegando a ese sitio."

            elif accion == "leer_pagina":
                contenido = navegador.leer_pagina()
                if contenido:
                    resumen = cerebro.resumir_pagina(contenido, texto_procesar)
                    mensaje = resumen
                else:
                    mensaje = "No pude leer el contenido de la página actual."

            elif accion == "mostrar_navegador":
                try:
                    navegador.mostrar()
                    mensaje = "Abriendo Opera GX en primer plano!"
                except Exception as e:
                    mensaje = "No pude abrir el navegador."

            elif accion == "apagar_pc":
                pc.apagar(reiniciar=False)

            elif accion == "reiniciar_pc":
                pc.apagar(reiniciar=True)

            elif accion == "cancelar_apagado":
                pc.cancelar_apagado()

            elif accion == "volumen" and subaccion:
                if not pc.volumen(subaccion, int(cantidad)):
                    mensaje = "No pude ajustar el volumen."

            elif accion == "brillo" and subaccion:
                if not pc.brillo(subaccion, int(cantidad)):
                    mensaje = "No pude ajustar el brillo. Solo funciona en laptops."

            elif accion == "claude_code":
                if prompt_claude:
                    pc.claude_code_con_prompt(prompt_claude)
                else:
                    pc.abrir("claude code")

            elif accion == "guardar_programa" and prog_nombre and prog_ruta:
                cerebro.memoria.setdefault("programas", {})[prog_nombre.lower()] = prog_ruta
                pc.programas_extra = cerebro.memoria["programas"]
                guardar_memoria(cerebro.memoria)

            elif accion == "guardar_memoria" and mem_key and mem_valor:
                if mem_key == "nombre":
                    cerebro.memoria["nombre"] = mem_valor
                elif mem_key == "preferencia":
                    if mem_valor not in cerebro.memoria["preferencias"]:
                        cerebro.memoria["preferencias"].append(mem_valor)
                elif mem_key == "nota":
                    if mem_valor not in cerebro.memoria["notas"]:
                        cerebro.memoria["notas"].append(mem_valor)
                guardar_memoria(cerebro.memoria)

            # ── Feature 3: Mouse / keyboard actions ──
            elif accion == "mouse_click":
                if mouse_x is not None and mouse_y is not None:
                    if not mouse.click(int(mouse_x), int(mouse_y)):
                        mensaje = "No pude hacer clic en esa posición."
                else:
                    mensaje = "Necesito las coordenadas para hacer clic."

            elif accion == "escribir_texto":
                if texto_escribir:
                    if not mouse.escribir(texto_escribir):
                        mensaje = "No pude escribir el texto."
                else:
                    mensaje = "No recibí el texto a escribir."

            elif accion == "hotkey":
                if teclas:
                    keys_list = [k.strip() for k in teclas.replace("+", " ").split()]
                    if not mouse.hotkey(*keys_list):
                        mensaje = "No pude ejecutar el atajo de teclado."
                else:
                    mensaje = "No recibí las teclas para el atajo."

            elif accion == "screenshot":
                descripcion = mouse.screenshot_y_analizar(texto_procesar, cerebro)
                mensaje = descripcion

            elif accion == "recordatorio" and rec_msg and rec_seg:
                recordatorios.agregar(rec_msg, int(rec_seg))

            elif accion == "estado_sistema":
                mensaje = monitor.estado()

            elif accion == "ventana" and vent_accion:
                if vent_accion == "listar":
                    mensaje = ventanas.listar()
                elif vent_accion == "enfocar":
                    mensaje = ventanas.enfocar(vent_nombre)
                elif vent_accion == "maximizar":
                    mensaje = ventanas.maximizar(vent_nombre)
                elif vent_accion == "minimizar":
                    mensaje = ventanas.minimizar(vent_nombre)
                elif vent_accion == "cerrar":
                    mensaje = ventanas.cerrar(vent_nombre)

            elif accion == "buscar_archivo" and archivo_buscar:
                voz.hablar(mensaje)
                resultados = archivos.buscar(archivo_buscar)
                if resultados:
                    nombres = [os.path.basename(r) for r in resultados[:3]]
                    mensaje = f"Encontré {len(resultados)} archivo(s): {', '.join(nombres)}. ¿Quieres que abra alguno?"
                    cerebro.historial.append({"role": "assistant", "content": f"Archivos encontrados: {resultados}"})
                else:
                    mensaje = f"No encontré ningún archivo con '{archivo_buscar}' en tus carpetas."

            elif accion == "whatsapp" and wa_contacto and wa_mensaje_txt:
                voz.hablar(mensaje)
                if whatsapp.enviar(wa_contacto, wa_mensaje_txt):
                    mensaje = f"Mensaje enviado a {wa_contacto}."
                else:
                    mensaje = f"No pude enviar el mensaje. Asegúrate de tener WhatsApp Web abierto y sesión iniciada."

            # ── Multi-step plan ──
            elif accion == "plan" and pasos:
                voz.hablar(mensaje)
                mensaje = cerebro.ejecutar_plan(pasos, texto_procesar, navegador, cerebro)

            # Hablar y esperar que termine antes de volver a escuchar
            hilo_voz = threading.Thread(target=voz.hablar, args=(mensaje,), daemon=True)
            hilo_voz.start()
            hilo_voz.join()
            time.sleep(0.4)  # pausa para que el eco del parlante se disipe

            turnos_activos += 1
            if turnos_activos >= 8:
                modo_activo = False

        except KeyboardInterrupt:
            print("\nApagando Jade...")
            voz.hablar("Hasta luego!")
            try:
                navegador.cerrar()
            except:
                pass
            break

if __name__ == "__main__":
    main()
