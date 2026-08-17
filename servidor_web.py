"""
SERVIDOR WEB — Alfred por voz desde el teléfono
=================================================
Expone una página web local para hablar con Alfred desde cualquier dispositivo
en tu red (o desde fuera de casa vía Tailscale). El navegador del teléfono
hace el reconocimiento de voz (Web Speech API) y le manda el texto reconocido
a este servidor; Alfred procesa el turno con el mismo "cerebro" que usa por
micrófono local (mismo historial de conversación, mismas acciones, mismo
vault), y devuelve la respuesta en audio (Edge TTS) para que la reproduzca
el teléfono.

Se activa desde asistente.py si en .env hay:
  WEB_SERVER_ENABLED=true
  WEB_SERVER_PORT=8420        (opcional, por defecto 8420)
  WEB_ACCESS_TOKEN=algo-secreto

Ver ALFRED_TELEFONO.md para la configuración completa con Tailscale.
"""

import os
import tempfile
import threading

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel


class TurnoRequest(BaseModel):
    texto: str


def _verificar_token(token_recibido, token_esperado):
    if not token_esperado:
        return  # sin token configurado: sin protección (no recomendado, avisamos al iniciar)
    if token_recibido != token_esperado:
        raise HTTPException(status_code=401, detail="Token inválido")


def crear_app(ctx, ejecutar_accion, token_esperado):
    app = FastAPI()
    lock = threading.Lock()

    @app.get("/", response_class=HTMLResponse)
    def pagina():
        return PAGINA_HTML

    @app.post("/hablar")
    def hablar(turno: TurnoRequest, authorization: str = Header(default="")):
        token = authorization.replace("Bearer ", "").strip()
        _verificar_token(token, token_esperado)
        texto = (turno.texto or "").strip()
        if not texto:
            raise HTTPException(status_code=400, detail="Texto vacío")
        with lock:
            resp, accion = ctx.cerebro.procesar(texto)
            mensaje = ejecutar_accion(resp, accion, texto, ctx)
        return {"mensaje": mensaje}

    @app.get("/tts")
    def tts(texto: str = Query(...), token: str = Query(default="")):
        _verificar_token(token, token_esperado)
        tmp = tempfile.mktemp(suffix=".mp3")
        try:
            ctx.voz._tts_a_archivo(texto, tmp)
            with open(tmp, "rb") as f:
                datos = f.read()
            return Response(content=datos, media_type="audio/mpeg")
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    return app


def iniciar_en_hilo(ctx, ejecutar_accion, puerto, token):
    """Arranca el servidor web en un hilo en segundo plano (no bloquea el loop de voz local)."""
    import uvicorn

    app = crear_app(ctx, ejecutar_accion, token)
    config = uvicorn.Config(app, host="0.0.0.0", port=puerto, log_level="warning")
    servidor = uvicorn.Server(config)
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    return hilo


PAGINA_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alfred</title>
<style>
  * { box-sizing: border-box; }
  body { background:#111; color:#eee; font-family: system-ui, -apple-system, sans-serif; margin:0; padding:1rem; min-height:100vh; }
  h1 { font-size:1.2rem; text-align:center; margin:.5rem 0 1rem; }
  #log { max-height:55vh; overflow-y:auto; margin-bottom:1rem; padding:.25rem; }
  .msg { padding:.6rem .9rem; margin:.4rem 0; border-radius:.8rem; max-width:85%; line-height:1.35; }
  .yo { background:#2a6b4f; margin-left:auto; text-align:right; }
  .alfred { background:#2a2a2a; }
  #boton { display:block; margin:1.5rem auto; width:5.5rem; height:5.5rem; border-radius:50%; border:none; background:#c0392b; color:#fff; font-size:2.2rem; }
  #boton.grabando { background:#27ae60; }
  #boton:disabled { background:#555; }
  #token { width:100%; padding:.6rem; margin-bottom:.75rem; border-radius:.4rem; border:1px solid #444; background:#1a1a1a; color:#eee; }
  #estado { text-align:center; color:#888; font-size:.85rem; min-height:1.2em; }
</style>
</head>
<body>
<h1>🤖 Alfred</h1>
<input id="token" type="password" placeholder="Token de acceso">
<div id="log"></div>
<button id="boton">🎤</button>
<div id="estado"></div>
<audio id="audio" hidden></audio>
<script>
const log = document.getElementById('log');
const boton = document.getElementById('boton');
const estado = document.getElementById('estado');
const audioEl = document.getElementById('audio');
const tokenEl = document.getElementById('token');
tokenEl.value = localStorage.getItem('alfred_token') || '';
tokenEl.addEventListener('change', () => localStorage.setItem('alfred_token', tokenEl.value));

function agregar(texto, quien) {
  const div = document.createElement('div');
  div.className = 'msg ' + quien;
  div.textContent = texto;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

const Recon = window.SpeechRecognition || window.webkitSpeechRecognition;
let recon = null;
if (!Recon) {
  estado.textContent = 'Tu navegador no soporta reconocimiento de voz. Prueba con Chrome.';
  boton.disabled = true;
} else {
  recon = new Recon();
  recon.lang = 'es-ES';
  recon.interimResults = false;
  recon.onresult = (e) => {
    const texto = e.results[0][0].transcript;
    agregar(texto, 'yo');
    enviar(texto);
  };
  recon.onerror = (e) => {
    estado.textContent = 'Error de reconocimiento: ' + e.error;
    boton.classList.remove('grabando');
  };
  recon.onend = () => boton.classList.remove('grabando');
}

boton.addEventListener('click', () => {
  if (!recon) return;
  boton.classList.add('grabando');
  estado.textContent = 'Escuchando...';
  recon.start();
});

async function enviar(texto) {
  estado.textContent = 'Alfred está pensando...';
  try {
    const r = await fetch('/hablar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tokenEl.value },
      body: JSON.stringify({ texto })
    });
    if (!r.ok) {
      estado.textContent = 'Error ' + r.status + (r.status === 401 ? ' (token incorrecto)' : '');
      return;
    }
    const data = await r.json();
    agregar(data.mensaje, 'alfred');
    estado.textContent = '';
    audioEl.src = '/tts?texto=' + encodeURIComponent(data.mensaje) + '&token=' + encodeURIComponent(tokenEl.value);
    audioEl.play().catch(() => {});
  } catch (err) {
    estado.textContent = 'No pude conectar con Alfred.';
  }
}
</script>
</body>
</html>
"""
