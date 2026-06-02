"""
JADE - VOICE ASSISTANT
======================
- ElevenLabs voice (Jessica)
- Wake word: "Jade"
- Background browser (Playwright)
- "show me" -> opens Opera GX
- Program control
- Python 3.14+ Windows

.env file:
  ANTHROPIC_API_KEY=sk-ant-...
  ELEVENLABS_API_KEY=...
"""

import os, sys, json, subprocess, tempfile, time
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav_io
import speech_recognition as sr
import anthropic
from pathlib import Path
from playsound3 import playsound

WAKE_WORD        = "jade"
ELEVENLABS_VOICE = "cgSgspJ2msm6clMCkdW9"
ELEVENLABS_MODEL = "eleven_turbo_v2"
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
    "opera":             OPERA_PATH,
    "opera gx":          OPERA_PATH,
    "browser":           OPERA_PATH,
    "chrome":            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":           r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vscode":            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "vs code":           r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "discord":           r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe",
    "spotify":           r"%APPDATA%\Spotify\Spotify.exe",
    "whatsapp":          r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe",
    "notepad":           "notepad.exe",
    "calculator":        "calc.exe",
    "explorer":          "explorer.exe",
    "task manager":      "taskmgr.exe",
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
# MICROPHONE
# ─────────────────────────────────────────

class Microfono:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16000
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5

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
            wav_io.write(path, self.sample_rate, data)
            with sr.AudioFile(path) as src:
                audio = self.recognizer.record(src)
            os.unlink(path)
            return self.recognizer.recognize_google(audio, language="en-US").lower().strip()
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Mic error: {e}")
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
        """Open Opera GX with current URL"""
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
# PC CONTROL
# ─────────────────────────────────────────

class ControlPC:
    def abrir(self, nombre):
        n = nombre.lower().strip()
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

# ─────────────────────────────────────────
# BRAIN
# ─────────────────────────────────────────

SYSTEM_PROMPT = """You are Jade, a personal voice assistant controlling a Windows PC.
ALWAYS respond in English only. Never use Spanish or any other language.

You can:
1. Open programs: LOL, Steam, Opera GX, Discord, Spotify, VSCode, etc.
2. Search the web in the background and report results
3. Navigate to specific websites
4. Answer questions and have natural conversation

RESPOND ONLY IN PURE JSON, NO MARKDOWN, NO EXPLANATION:
{"accion":"abrir_programa"|"buscar_web"|"navegar_url"|"mostrar_navegador"|"responder","programa":"name or null","query":"search query or null","url":"url or null","mensaje":"English only, max 2 sentences"}

EXAMPLES:
"open lol" -> {"accion":"abrir_programa","programa":"lol","query":null,"url":null,"mensaje":"Sure, opening League of Legends!"}
"open steam" -> {"accion":"abrir_programa","programa":"steam","query":null,"url":null,"mensaje":"Opening Steam right now!"}
"search flights to Brazil" -> {"accion":"buscar_web","programa":null,"query":"cheap flights to Brazil 2025","url":null,"mensaje":"Searching for flights to Brazil in the background, give me a second."}
"go to youtube" -> {"accion":"navegar_url","programa":null,"query":null,"url":"youtube.com","mensaje":"Navigating to YouTube now."}
"show me" -> {"accion":"mostrar_navegador","programa":null,"query":null,"url":null,"mensaje":"Opening Opera GX so you can see!"}
"how are you" -> {"accion":"responder","programa":null,"query":null,"url":null,"mensaje":"All good, ready to help!"}"""

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
                max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=self.historial
            )
            raw = r.content[0].text.strip().replace("```json","").replace("```","").strip()
            print(f"[DEBUG] {raw}")
            self.historial.append({"role": "assistant", "content": raw})
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"accion":"responder","programa":None,"query":None,"url":None,"mensaje":"One moment, I had an issue."}
        except Exception as e:
            print(f"[ERROR API] {e}")
            return {"accion":"responder","programa":None,"query":None,"url":None,"mensaje":"Connection issue, try again."}

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print("\n" + "="*52)
    print("   🤖  Jade — Voice Assistant  |  Windows")
    print("="*52 + "\n")

    keys = cargar_env()
    if "ANTHROPIC_API_KEY" not in keys:
        print("❌ Missing ANTHROPIC_API_KEY in .env"); sys.exit(1)
    if "ELEVENLABS_API_KEY" not in keys:
        print("❌ Missing ELEVENLABS_API_KEY in .env"); sys.exit(1)

    print("🔧 Starting up...\n")
    voz      = Voz(keys["ELEVENLABS_API_KEY"])
    mic      = Microfono()
    pc       = ControlPC()
    cerebro  = Cerebro(keys["ANTHROPIC_API_KEY"])

    print("🌐 Starting background browser...")
    navegador = Navegador()

    print(f"\n✅ Ready! Say '{WAKE_WORD.upper()}' to activate | Ctrl+C to quit\n")
    print("-"*52)

    voz.hablar("Hey! I am Jade, your personal assistant. Call my name whenever you need me.")

    modo_activo    = False
    turnos_activos = 0

    while True:
        try:
            texto = mic.escuchar()
            if not texto:
                modo_activo = False
                continue

            print(f"👤 [{'ON' if modo_activo else 'standby'}] {texto}")

            # ── Standby: wait for wake word ──
            if not modo_activo:
                if WAKE_WORD in texto:
                    modo_activo    = True
                    turnos_activos = 0
                    comando = texto.replace(WAKE_WORD, "").strip()
                    if len(comando) > 3:
                        texto_procesar = comando
                    else:
                        voz.hablar("Yeah?")
                        continue
                else:
                    continue
            else:
                texto_procesar = texto

            # ── Deactivate ──
            if any(p in texto for p in ["goodbye","bye jade","thanks jade","ok thanks","stop listening"]):
                voz.hablar("Got it, call me when you need me!")
                modo_activo = False
                continue

            resp     = cerebro.procesar(texto_procesar)
            accion   = resp.get("accion")
            programa = resp.get("programa")
            query    = resp.get("query")
            url      = resp.get("url")
            mensaje  = resp.get("mensaje", "Done!")

            if accion == "abrir_programa" and programa:
                if not pc.abrir(programa):
                    mensaje = f"I couldn't find {programa}. Make sure it's installed."

            elif accion == "buscar_web" and query:
                voz.hablar(mensaje)
                try:
                    resultados = navegador.buscar_google(query)
                    if resultados:
                        resumen = ". ".join(resultados[:2])
                        mensaje = f"Here's what I found: {resumen}. Say show me to open Opera GX."
                    else:
                        mensaje = "I searched but couldn't find clear results. Say show me to check the browser."
                except Exception as e:
                    print(f"[ERROR BROWSER] {e}")
                    mensaje = "I had trouble with the browser, try again."

            elif accion == "navegar_url" and url:
                voz.hablar(mensaje)
                try:
                    title = navegador.navegar(url)
                    mensaje = f"I'm on {title} now. Say show me if you want to see it."
                except Exception as e:
                    print(f"[ERROR NAV] {e}")
                    mensaje = f"I had trouble navigating there."

            elif accion == "mostrar_navegador":
                try:
                    navegador.mostrar()
                    mensaje = "Opening Opera GX now!"
                except Exception as e:
                    print(f"[ERROR SHOW] {e}")
                    mensaje = "I couldn't open the browser."

            voz.hablar(mensaje)

            turnos_activos += 1
            if turnos_activos >= 4:
                modo_activo = False

        except KeyboardInterrupt:
            print("\nShutting down Jade...")
            voz.hablar("See you later!")
            try:
                navegador.cerrar()
            except:
                pass
            break

if __name__ == "__main__":
    main()
