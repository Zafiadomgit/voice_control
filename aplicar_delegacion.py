"""Aplica el cambio de delegacion a Claude Code directo sobre asistente.py local."""
from pathlib import Path

ruta = Path(__file__).parent / "asistente.py"
texto = ruta.read_text(encoding="utf-8")

VIEJO = """14. Buscar archivos en el PC por nombre
15. Enviar mensajes de WhatsApp por voz
16. Listar ventanas abiertas

RESPONDE SOLO EN JSON PURO, SIN MARKDOWN, SIN EXPLICACIÓN:"""

NUEVO = """14. Buscar archivos en el PC por nombre
15. Enviar mensajes de WhatsApp por voz
16. Listar ventanas abiertas
17. Delegar a Claude Code cualquier tarea real sobre el PC que no esté en esta lista

CUÁNDO DELEGAR A CLAUDE CODE:
Esta lista de acciones no lo cubre todo. Si te piden una TAREA CONCRETA sobre el PC, archivos, código o internet que no está arriba (instalar un programa, escribir o editar código, organizar carpetas, automatizar algo nuevo, investigar y resolver un problema técnico paso a paso), usa la acción "claude_code" con "prompt_claude" describiendo la tarea completa en una instrucción autónoma y clara — Claude Code no vio esta conversación, así que dale todo el contexto necesario para que pueda trabajar solo. Claude Code tiene acceso real a archivos, terminal e internet: puede hacer casi cualquier cosa en el PC. Nunca respondas "no sé cómo hacer eso" ni "no tengo esa capacidad" — delega.
No delegues conversación normal, preguntas generales, opiniones, ni nada que ya puedas resolver con tus propias acciones — solo tareas reales que requieran manos en el sistema y que no estén en tu lista.
Ejemplos:
"instálame un lector de PDF" -> {"accion":"claude_code","prompt_claude":"Instala un lector de PDF gratuito y liviano para Windows, y crea un acceso directo en el escritorio.","mensaje":"Le paso la tarea a Claude Code, dame un momento."}
"organiza mis descargas por tipo de archivo" -> {"accion":"claude_code","prompt_claude":"Organiza la carpeta Downloads del usuario en subcarpetas por tipo de archivo (PDFs, imágenes, videos, instaladores, comprimidos, etc.).","mensaje":"Abriendo Claude Code para que ordene tus descargas."}
"revisa por qué mi otro proyecto no compila y arréglalo" -> {"accion":"claude_code","prompt_claude":"El usuario reporta que su proyecto no compila. Investiga la causa en la carpeta del proyecto y corrígela.","mensaje":"Le paso el problema a Claude Code para que lo investigue y lo arregle."}

RESPONDE SOLO EN JSON PURO, SIN MARKDOWN, SIN EXPLICACIÓN:"""

n = texto.count(VIEJO)
if n == 0:
    print("❌ No encontré el bloque esperado — puede que asistente.py ya tenga este cambio, o difiera del original. No toqué nada.")
elif n > 1:
    print(f"⚠️ Encontré el bloque {n} veces (esperaba 1) — no toqué nada, avisa a Claude.")
else:
    ruta.write_text(texto.replace(VIEJO, NUEVO), encoding="utf-8")
    print("✅ asistente.py actualizado con la delegación a Claude Code.")
