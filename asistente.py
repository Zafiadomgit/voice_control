"""
JADE - VOICE ASSISTANT
======================
- ElevenLabs voice (Laura, multilingual)
- Wake word: "Jade" (flexible, standby sensible)
- Background browser (Playwright) + DuckDuckGo search
- Program control + PC control (shutdown, restart, volume, brightness)
- Claude Code integration via voice
- Google STT (español)
- Memoria persistente (nombre, preferencias)
- Python 3.10+ Windows

.env file:
  ANTHROPIC_API_KEY=sk-ant-...
  ELEVENLABS_API_KEY=...
"""

import os, sys, json, subprocess, tempfile, time, threading
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav_io
import anthropic
from pathlib import Path
from playsound3 import playsound

WAKE_WORD        = "jade"
ELEVENLABS_VOICE = "FGY2WhTYpPnrIDTdsKH5"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
OPERA_PATH       = r"C:\Users\david\AppData\Local\Programs\Opera GX\opera.exe"
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
    for k in ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]:
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
    return {"nombre": None, "preferencias": [], "notas": []}

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
    return "\n".join(partes) if partes else ""

# ─────────────────────────────────────────
# PROGRAMS
# ─────────────────────────────────────────

PROGRAMAS = {
    "lol":               r"C:\Riot Games\League of Legends\LeagueClient.exe",
    "league":            r"C:\Riot Games\League of Legends\LeagueClient.exe",
    "league of legends": r"C:\Riot Games\League of Legends\LeagueClient.exe",
    "valorant":          r"C:\Riot Games\VALORANT\live\VALORANT.exe",
    "steam":             r"C:\Program Files (x86)\Steam\steam.exe",
    "epic games":        r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "epic":              r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "opera":             OPERA_PATH,
    "opera gx":          OPERA_PATH,
    "browser":           OPERA_PATH,
    "navegador":         OPERA_PATH,
    "chrome":            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":           r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vscode":            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "vs code":           r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "visual studio":     r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "discord":           r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe",
    "spotify":           r"%APPDATA%\Spotify\Spotify.exe",
    "whatsapp":          r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe",
    "notepad":           "notepad.exe",
    "bloc de notas":     "notepad.exe",
    "calculator":        "calc.exe",
    "calculadora":       "calc.exe",
    "explorer":          "explorer.exe",
    "explorador":        "explorer.exe",
    "task manager":      "taskmgr.exe",
    "administrador de tareas": "taskmgr.exe",
    "claude":            r"%LOCALAPPDATA%\Programs\claude\Claude.exe",
    "claude code":       "cmd.exe",
}

# ─────────────────────────────────────────
# VOICE
# ─────────────────────────────────────────

class Voz:
    def __init__(self, api_key):
        self.api_key    = api_key
        self._hablando  = False
        self._stop_flag = threading.Event()

    def interrumpir(self):
        self._stop_flag.set()

    def hablar(self, texto):
        print(f"\n🔊 Jade: {texto}\n")
        self._stop_flag.clear()
        self._hablando = True
        tmp = None
        try:
            import urllib.request
            payload = json.dumps({
                "text": texto,
                "model_id": ELEVENLABS_MODEL,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                    "use_speaker_boost": True
                }
            }).encode("utf-8")
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
                data=payload, method="POST"
            )
            req.add_header("xi-api-key", self.api_key)
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "audio/mpeg")
            with urllib.request.urlopen(req) as resp:
                audio = resp.read()
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
                f.write(audio)
            if not self._stop_flag.is_set():
                t = threading.Thread(target=playsound, args=(tmp,), daemon=True)
                t.start()
                t.join(timeout=30)
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
                    time.sleep(0.3)
                    os.unlink(tmp)
                except:
                    pass

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
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
            for _ in range(chunks_max):
                data, _ = stream.read(chunk)
                grabando.append(data.copy())
                vol = float(np.abs(data).mean())
                if vol > 0.007:
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
        return (np.concatenate(grabando) * 32767).astype(np.int16)

    def escuchar(self, modo_standby=False):
        try:
            # En standby: frases cortas, corta rápido
            if modo_standby:
                data = self.grabar(max_segundos=4, silencio_segundos=0.6, timeout_sin_voz=1.5)
            else:
                data = self.grabar(max_segundos=10, silencio_segundos=1.2, timeout_sin_voz=2.5)

            if len(data) < 1500:
                return None

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                path = f.name
            wav_io.write(path, self.sample_rate, data)

            import speech_recognition as sr
            with sr.AudioFile(path) as src:
                audio = self.recognizer.record(src)
            os.unlink(path)
            return self.recognizer.recognize_google(audio, language="es-ES").lower().strip()
        except Exception:
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
            titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if t.strip()]
            titles = [t for t in titles if len(t) > 5][:3]
            return titles
        except Exception as e:
            print(f"[ERROR SEARCH] {e}")
            return []

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
        for k, v in PROGRAMAS.items():
            if k in n or n in k:
                ruta = os.path.expandvars(v)
                try:
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(None, "open", ruta, None, None, 1)
                    return True
                except:
                    try:
                        subprocess.Popen(ruta, shell=True)
                        return True
                    except:
                        pass
        try:
            subprocess.Popen(n, shell=True)
            return True
        except:
            return False

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
# BRAIN
# ─────────────────────────────────────────

SYSTEM_PROMPT_BASE = """Eres Jade, una asistente de voz personal que controla un PC con Windows.
Respondes siempre en español, con naturalidad y brevedad.

{memoria}

Puedes hacer:
1. Abrir programas: LOL, Steam, Opera GX, Discord, Spotify, VSCode, Chrome, WhatsApp, Claude, Claude Code, etc.
2. Buscar en la web y reportar resultados
3. Navegar a sitios web
4. Controlar el PC: apagar, reiniciar, volumen, brillo
5. Abrir Claude Code con un prompt de voz
6. Recordar información del usuario (nombre, preferencias, notas)
7. Conversación natural

RESPONDE SOLO EN JSON PURO, SIN MARKDOWN, SIN EXPLICACIÓN:
{"accion":"abrir_programa"|"buscar_web"|"navegar_url"|"mostrar_navegador"|"apagar_pc"|"reiniciar_pc"|"cancelar_apagado"|"volumen"|"brillo"|"claude_code"|"guardar_memoria"|"responder",
 "programa":"nombre o null",
 "query":"búsqueda o null",
 "url":"url o null",
 "subaccion":"subir"|"bajar"|"silenciar"|"activar"|"establecer" o null,
 "cantidad":número o null,
 "prompt_claude":"tarea para claude code o null",
 "memoria_key":"nombre"|"preferencia"|"nota" o null,
 "memoria_valor":"valor a guardar o null",
 "mensaje":"respuesta en español, máximo 2 oraciones"}

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

    def procesar(self, texto):
        self.historial.append({"role": "user", "content": texto})
        if len(self.historial) > 20:
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
    if "ELEVENLABS_API_KEY" not in keys:
        print("❌ Falta ELEVENLABS_API_KEY en .env"); sys.exit(1)

    memoria  = cargar_memoria()
    print(f"🧠 Memoria cargada: {memoria}")

    print("🔧 Iniciando...\n")
    voz      = Voz(keys["ELEVENLABS_API_KEY"])
    mic      = Microfono()
    pc       = ControlPC()
    cerebro  = Cerebro(keys["ANTHROPIC_API_KEY"], memoria)

    print("🌐 Iniciando navegador en segundo plano...")
    navegador = Navegador()

    nombre = memoria.get("nombre") or "usuario"
    print(f"\n✅ Listo! Di 'JADE' para activarme | Ctrl+C para salir\n")
    print("-"*52)

    saludo = f"Hola {nombre}! Aquí estoy." if memoria.get("nombre") else "Hola! Soy Jade, tu asistente personal. Llámame cuando me necesites."
    voz.hablar(saludo)

    modo_activo    = False
    turnos_activos = 0
    ultimo_texto   = 0
    WAKE_WORDS     = ["jade", "jad", "yade"]

    hilo_voz = None

    while True:
        try:
            # Escuchar en hilo separado mientras Jade habla (para poder interrumpir)
            texto = mic.escuchar(modo_standby=not modo_activo)

            if not texto:
                if modo_activo and (time.time() - ultimo_texto > 15):
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

            resp          = cerebro.procesar(texto_procesar)
            accion        = resp.get("accion")
            programa      = resp.get("programa")
            query         = resp.get("query")
            url           = resp.get("url")
            subaccion     = resp.get("subaccion")
            cantidad      = resp.get("cantidad") or 10
            prompt_claude = resp.get("prompt_claude")
            mem_key       = resp.get("memoria_key")
            mem_valor     = resp.get("memoria_valor")
            mensaje       = resp.get("mensaje", "Hecho!")

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

            hilo_voz = threading.Thread(target=voz.hablar, args=(mensaje,), daemon=True)
            hilo_voz.start()
            hilo_voz.join()  # esperar a que termine antes del próximo ciclo

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
