"""
JADE - VOICE ASSISTANT
======================
- ElevenLabs voice (Jessica)
- Wake word: "Jade"
- Background browser (Playwright)
- "show me" / "muéstrame" -> opens Opera GX
- Program control
- PC control (shutdown, restart, volume, brightness)
- Claude Code integration via voice
- Whisper local STT (faster-whisper)
- Spanish + English
- Python 3.10+ Windows

.env file:
  ANTHROPIC_API_KEY=sk-ant-...
  ELEVENLABS_API_KEY=...
"""

import os, sys, json, subprocess, tempfile, time
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
        self.api_key = api_key

    def hablar(self, texto):
        print(f"\n🔊 Jade: {texto}\n")
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
            playsound(tmp)
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
            if tmp:
                try:
                    time.sleep(0.2)
                    os.unlink(tmp)
                except:
                    pass

# ─────────────────────────────────────────
# MICROPHONE — Whisper local STT
# ─────────────────────────────────────────

class Microfono:
    def __init__(self):
        self.sample_rate = 16000
        self._init_whisper()

    def _init_whisper(self):
        try:
            from faster_whisper import WhisperModel
            # base model: good balance of speed/accuracy; change to "small" for more accuracy
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
            self.usar_whisper = True
            print("🎙️  Whisper local STT ready (base model)")
        except ImportError:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 200
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.5
            self.usar_whisper = False
            print("🎙️  Using Google STT (install faster-whisper for local STT)")

    def grabar(self):
        chunk = int(self.sample_rate * 0.05)
        chunks_sil = int(1.2 / 0.05)
        chunks_max = int(15 / 0.05)
        grabando, silencio, hablo = [], 0, False
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
            for _ in range(chunks_max):
                data, _ = stream.read(chunk)
                grabando.append(data.copy())
                vol = float(np.abs(data).mean())
                if vol > 0.007:
                    hablo = True
                    silencio = 0
                elif hablo:
                    silencio += 1
                    if silencio >= chunks_sil:
                        break
        return (np.concatenate(grabando) * 32767).astype(np.int16)

    def escuchar(self):
        try:
            data = self.grabar()
            if len(data) < 2000:
                return None

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                path = f.name
            import scipy.io.wavfile as wav_io
            wav_io.write(path, self.sample_rate, data)

            if self.usar_whisper:
                texto = self._transcribir_whisper(path)
            else:
                texto = self._transcribir_google(path)

            os.unlink(path)
            return texto
        except Exception as e:
            print(f"Mic error: {e}")
            return None

    def _transcribir_whisper(self, path):
        try:
            segments, info = self.model.transcribe(
                path,
                language="es",
                beam_size=5,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
                initial_prompt="Jade asistente de voz. Comandos en español.",
            )
            partes = [s.text.strip() for s in segments]
            # quitar repeticiones consecutivas
            sin_repeticiones = []
            for p in partes:
                if not sin_repeticiones or p.lower() != sin_repeticiones[-1].lower():
                    sin_repeticiones.append(p)
            resultado = " ".join(sin_repeticiones).strip().lower()
            if not resultado or len(resultado) < 2:
                return None
            return resultado
        except Exception as e:
            print(f"[WHISPER ERROR] {e}")
            return None

    def _transcribir_google(self, path):
        try:
            import speech_recognition as sr
            with sr.AudioFile(path) as src:
                audio = self.recognizer.record(src)
            return self.recognizer.recognize_google(audio, language="es-ES").lower().strip()
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[GOOGLE STT ERROR] {e}")
            return None

# ─────────────────────────────────────────
# BROWSER — Playwright sync, headless
# ─────────────────────────────────────────

class Navegador:
    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw     = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page    = self.context.new_page()
        print("🌐 Background browser ready")

    def mostrar(self):
        try:
            url = self.page.evaluate("window.location.href")
            if os.path.exists(OPERA_PATH):
                subprocess.Popen([OPERA_PATH, url])
            else:
                os.startfile(url)
            return url
        except Exception as e:
            print(f"[ERROR SHOW] {e}")
            return None

    def buscar_google(self, query):
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            self.page.wait_for_timeout(2000)
            results = self.page.evaluate("""() => {
                const items = document.querySelectorAll('h3');
                return Array.from(items).slice(0,3).map(h=>h.innerText).filter(t=>t.length>0);
            }""")
            return results
        except Exception as e:
            print(f"[ERROR SEARCH] {e}")
            return []

    def navegar(self, url):
        try:
            if not url.startswith("http"):
                url = "https://" + url
            self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            self.page.wait_for_timeout(2000)
            return self.page.title()
        except Exception as e:
            print(f"[ERROR NAV] {e}")
            return url

    def leer_pagina(self):
        try:
            return self.page.evaluate("""() => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script,style,nav,footer,header').forEach(e=>e.remove());
                return clone.innerText.substring(0,2000);
            }""")
        except:
            return ""

    def cerrar(self):
        try:
            self.browser.close()
            self._pw.stop()
        except:
            pass

# ─────────────────────────────────────────
# PC CONTROL — programs, shutdown, volume, brightness, Claude Code
# ─────────────────────────────────────────

class ControlPC:
    def abrir(self, nombre):
        n = nombre.lower().strip()

        # Special: open Claude Code in a new terminal window
        if "claude code" in n or "claude código" in n:
            return self._abrir_claude_code()

        for k, v in PROGRAMAS.items():
            if k in n or n in k:
                ruta = os.path.expandvars(v)
                try:
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(None, "open", ruta, None, None, 1)
                    return True
                except Exception as e:
                    print(f"Error opening {k}: {e}")
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
            cmd = "claude"
            if prompt:
                cmd = f'claude "{prompt}"'
            subprocess.Popen(
                f'start cmd /k {cmd}',
                shell=True
            )
            return True
        except Exception as e:
            print(f"[ERROR CLAUDE CODE] {e}")
            return False

    def claude_code_con_prompt(self, prompt):
        return self._abrir_claude_code(prompt=prompt)

    def apagar(self, reiniciar=False):
        try:
            if reiniciar:
                subprocess.Popen("shutdown /r /t 10", shell=True)
            else:
                subprocess.Popen("shutdown /s /t 10", shell=True)
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
        """accion: 'subir' | 'bajar' | 'silenciar' | 'activar'"""
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
            # Fallback: use nircmd if pycaw not available
            try:
                if accion == "subir":
                    subprocess.Popen(f"nircmd changedefaultsounddevice volume +{cantidad*655}", shell=True)
                elif accion == "bajar":
                    subprocess.Popen(f"nircmd changedefaultsounddevice volume -{cantidad*655}", shell=True)
                elif accion == "silenciar":
                    subprocess.Popen("nircmd mutesysvolume 1", shell=True)
                elif accion == "activar":
                    subprocess.Popen("nircmd mutesysvolume 0", shell=True)
                return True
            except:
                print(f"[ERROR VOLUME] {e}")
                return False

    def brillo(self, accion, cantidad=10):
        """accion: 'subir' | 'bajar' | 'establecer'; cantidad: 0-100"""
        try:
            import wmi
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            brightness_obj = c.WmiMonitorBrightness()[0]
            current = brightness_obj.CurrentBrightness

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

SYSTEM_PROMPT = """Eres Jade, una asistente de voz personal que controla un PC con Windows.
Respondes en español. Si el usuario habla en inglés, igual respondes en español.

Puedes hacer:
1. Abrir programas: LOL, Steam, Opera GX, Discord, Spotify, VSCode, Chrome, WhatsApp, Claude, Claude Code, etc.
2. Buscar en la web en segundo plano y reportar resultados
3. Navegar a sitios web específicos
4. Controlar el PC: apagar, reiniciar, subir/bajar volumen, subir/bajar brillo
5. Abrir Claude Code con un prompt específico para programar
6. Responder preguntas y mantener conversación natural

RESPONDE SOLO EN JSON PURO, SIN MARKDOWN, SIN EXPLICACIÓN:
{"accion":"abrir_programa"|"buscar_web"|"navegar_url"|"mostrar_navegador"|"apagar_pc"|"reiniciar_pc"|"cancelar_apagado"|"volumen"|"brillo"|"claude_code"|"responder",
 "programa":"nombre o null",
 "query":"búsqueda o null",
 "url":"url o null",
 "subaccion":"subir"|"bajar"|"silenciar"|"activar"|"establecer" o null,
 "cantidad":número o null,
 "prompt_claude":"tarea para claude code o null",
 "mensaje":"respuesta en español, máximo 2 oraciones"}

EJEMPLOS:
"jade abre el lol" -> {"accion":"abrir_programa","programa":"lol","query":null,"url":null,"subaccion":null,"cantidad":null,"prompt_claude":null,"mensaje":"Claro, abriendo League of Legends!"}
"jade busca vuelos a Brasil" -> {"accion":"buscar_web","programa":null,"query":"vuelos baratos a Brasil 2025","url":null,"subaccion":null,"cantidad":null,"prompt_claude":null,"mensaje":"Buscando vuelos a Brasil, dame un segundo."}
"jade apaga el pc" -> {"accion":"apagar_pc","programa":null,"query":null,"url":null,"subaccion":null,"cantidad":null,"prompt_claude":null,"mensaje":"Apagando el PC en 10 segundos. Di cancela si te arrepentiste."}
"jade reinicia" -> {"accion":"reiniciar_pc","programa":null,"query":null,"url":null,"subaccion":null,"cantidad":null,"prompt_claude":null,"mensaje":"Reiniciando el PC en 10 segundos."}
"jade sube el volumen" -> {"accion":"volumen","programa":null,"query":null,"url":null,"subaccion":"subir","cantidad":10,"prompt_claude":null,"mensaje":"Subiendo el volumen."}
"jade silencia" -> {"accion":"volumen","programa":null,"query":null,"url":null,"subaccion":"silenciar","cantidad":null,"prompt_claude":null,"mensaje":"Silenciando el audio."}
"jade baja el brillo" -> {"accion":"brillo","programa":null,"query":null,"url":null,"subaccion":"bajar","cantidad":10,"prompt_claude":null,"mensaje":"Bajando el brillo."}
"jade abre claude code y crea un script de python" -> {"accion":"claude_code","programa":null,"query":null,"url":null,"subaccion":null,"cantidad":null,"prompt_claude":"crea un script de python que...","mensaje":"Abriendo Claude Code con tu tarea."}
"jade muéstrame" -> {"accion":"mostrar_navegador","programa":null,"query":null,"url":null,"subaccion":null,"cantidad":null,"prompt_claude":null,"mensaje":"Abriendo Opera GX para que veas!"}"""

class Cerebro:
    def __init__(self, api_key):
        self.client    = anthropic.Anthropic(api_key=api_key)
        self.historial = []

    def procesar(self, texto):
        self.historial.append({"role": "user", "content": texto})
        if len(self.historial) > 20:
            self.historial = self.historial[-20:]
        try:
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=self.historial
            )
            raw = r.content[0].text.strip().replace("```json","").replace("```","").strip()
            print(f"[DEBUG] {raw}")
            self.historial.append({"role": "assistant", "content": raw})
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"accion":"responder","programa":None,"query":None,"url":None,"subaccion":None,"cantidad":None,"prompt_claude":None,"mensaje":"Un momento, tuve un problema procesando eso."}
        except Exception as e:
            print(f"[ERROR API] {e}")
            return {"accion":"responder","programa":None,"query":None,"url":None,"subaccion":None,"cantidad":None,"prompt_claude":None,"mensaje":"Problemas de conexión, intenta de nuevo."}

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

    print("🔧 Iniciando...\n")
    voz      = Voz(keys["ELEVENLABS_API_KEY"])
    mic      = Microfono()
    pc       = ControlPC()
    cerebro  = Cerebro(keys["ANTHROPIC_API_KEY"])

    print("🌐 Iniciando navegador en segundo plano...")
    navegador = Navegador()

    print(f"\n✅ Listo! Di '{WAKE_WORD.upper()}' para activarme | Ctrl+C para salir\n")
    print("-"*52)

    voz.hablar("Hola! Soy Jade, tu asistente personal. Llámame cuando me necesites.")

    modo_activo      = False
    turnos_activos   = 0
    ultimo_texto     = 0

    while True:
        try:
            texto = mic.escuchar()

            # En standby: silencio no hace nada
            # En modo activo: si pasan 15s sin hablar, vuelve a standby
            if not texto:
                if modo_activo and (time.time() - ultimo_texto > 15):
                    print("[timeout] Volviendo a standby")
                    modo_activo = False
                continue

            ultimo_texto = time.time()
            print(f"👤 [{'ON' if modo_activo else 'standby'}] {texto}")

            # ── Standby: esperar wake word ──
            WAKE_WORDS = ["jade", "jad", "yade", "yad"]
            if not modo_activo:
                if any(w in texto for w in WAKE_WORDS):
                    modo_activo    = True
                    turnos_activos = 0
                    # quitar el wake word del texto
                    comando = texto
                    for w in WAKE_WORDS:
                        comando = comando.replace(w, "").strip()
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
            mensaje       = resp.get("mensaje", "Hecho!")

            if accion == "abrir_programa" and programa:
                if not pc.abrir(programa):
                    mensaje = f"No encontré {programa}. Asegúrate de que esté instalado."

            elif accion == "buscar_web" and query:
                voz.hablar(mensaje)
                try:
                    resultados = navegador.buscar_google(query)
                    if resultados:
                        resumen = ". ".join(resultados[:2])
                        mensaje = f"Esto es lo que encontré: {resumen}. Di muéstrame para abrir Opera GX."
                    else:
                        mensaje = "Busqué pero no encontré resultados claros. Di muéstrame para ver el navegador."
                except Exception as e:
                    print(f"[ERROR BROWSER] {e}")
                    mensaje = "Tuve un problema con el navegador, intenta de nuevo."

            elif accion == "navegar_url" and url:
                voz.hablar(mensaje)
                try:
                    title = navegador.navegar(url)
                    mensaje = f"Estoy en {title}. Di muéstrame si quieres verlo."
                except Exception as e:
                    print(f"[ERROR NAV] {e}")
                    mensaje = "Tuve un problema navegando a ese sitio."

            elif accion == "mostrar_navegador":
                try:
                    navegador.mostrar()
                    mensaje = "Abriendo Opera GX!"
                except Exception as e:
                    print(f"[ERROR SHOW] {e}")
                    mensaje = "No pude abrir el navegador."

            elif accion == "apagar_pc":
                if pc.apagar(reiniciar=False):
                    mensaje = mensaje
                else:
                    mensaje = "No pude iniciar el apagado."

            elif accion == "reiniciar_pc":
                if pc.apagar(reiniciar=True):
                    mensaje = mensaje
                else:
                    mensaje = "No pude reiniciar el PC."

            elif accion == "cancelar_apagado":
                pc.cancelar_apagado()

            elif accion == "volumen" and subaccion:
                if not pc.volumen(subaccion, int(cantidad)):
                    mensaje = "No pude ajustar el volumen. Puede que necesites instalar pycaw."

            elif accion == "brillo" and subaccion:
                if not pc.brillo(subaccion, int(cantidad)):
                    mensaje = "No pude ajustar el brillo. Solo funciona en laptops con pantalla integrada."

            elif accion == "claude_code":
                if prompt_claude:
                    pc.claude_code_con_prompt(prompt_claude)
                else:
                    pc.abrir("claude code")

            voz.hablar(mensaje)

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
