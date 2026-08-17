# Hablarle a Alfred desde el teléfono

Alfred puede correr un servidor web local en tu PC: el teléfono se conecta a
una página simple que graba tu voz (el reconocimiento de voz corre en el
propio navegador del teléfono) y le manda el texto a Alfred, que procesa el
turno con el mismo cerebro y memoria que usa por micrófono local, y devuelve
la respuesta en audio.

El PC sigue siendo el que hace todo el trabajo (abrir programas, controlar
ventanas, etc.) — el teléfono es solo micrófono y bocina remotos. Por eso
para que funcione fuera de tu casa (no en la misma WiFi), necesitas una red
privada entre tu teléfono y tu PC: para eso es **Tailscale**.

## 1. Instalar y conectar Tailscale

1. Crea una cuenta gratis en [tailscale.com](https://tailscale.com) (puedes usar tu cuenta de Google/Microsoft).
2. Instala Tailscale en tu PC (Windows) y entra con esa cuenta.
3. Instala la app de Tailscale en tu teléfono (Android/iOS) y entra con la **misma cuenta**.
4. En tu PC, abre PowerShell o Git Bash y corre:
   ```
   tailscale ip -4
   ```
   Eso te da una IP tipo `100.x.x.x` — es la dirección de tu PC dentro de tu red privada de Tailscale, solo visible entre tus propios dispositivos. Apúntala.

No necesitas abrir ni redirigir ningún puerto en tu router — Tailscale hace el túnel privado directamente.

## 2. Configurar Alfred

En tu `.env` (dentro de `voice_control_repo`):

```
WEB_SERVER_ENABLED=true
WEB_SERVER_PORT=8420
WEB_ACCESS_TOKEN=elige-algo-largo-y-dificil-de-adivinar
```

El `WEB_ACCESS_TOKEN` es la contraseña para hablarle a Alfred por esta vía —
sin él, cualquiera dentro de tu red (o tu tailnet) podría controlar tu PC por
voz. No lo compartas ni lo subas a GitHub (el `.env` ya está en `.gitignore`).

Instala las dependencias nuevas si no lo has hecho:
```bash
python -m pip install -r requirements.txt
```

## 3. Arrancar y probar

Arranca Alfred normal:
```bash
python asistente.py
```
En la consola deberías ver:
```
📱 Servidor web para el teléfono activo en el puerto 8420 (usa tu IP de Tailscale + ese puerto desde el navegador del teléfono).
```

Desde el navegador de tu teléfono (con Tailscale activo en el teléfono),
entra a:
```
http://100.x.x.x:8420
```
(reemplaza `100.x.x.x` por la IP que sacaste en el paso 1). Pega tu
`WEB_ACCESS_TOKEN` en el campo de arriba, toca el botón del micrófono, y
habla — no hace falta decir "Alfred" primero, cada vez que tocas el botón ya
está escuchando activamente.

**Nota sobre navegadores:** el reconocimiento de voz del lado del teléfono
usa la Web Speech API — funciona bien en Chrome/Edge (Android e iOS). Safari
en iPhone tiene soporte más limitado; si no te reconoce la voz, prueba con
Chrome.

## Notas de seguridad

- El servidor escucha en todas las interfaces de red del PC (`0.0.0.0`), lo
  cual incluye tu WiFi normal además de Tailscale — pero como no hay ningún
  reenvío de puertos hacia internet, en la práctica solo es alcanzable desde
  tu misma red local o tu tailnet privada.
- **Nunca** configures reenvío de puertos (port forwarding) en tu router
  para el puerto 8420 — eso sí lo expondría a todo internet. Usa siempre
  Tailscale para el acceso remoto.
- Si alguna vez sospechas que el token se filtró, cámbialo en `.env` y
  reinicia Alfred.
