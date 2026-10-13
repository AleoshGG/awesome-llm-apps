"""HTML presentation adapter for the printable Neurotry card."""

from __future__ import annotations

from html import escape


class HtmlBusinessCardRenderer:
    def render(self, state: dict[str, object]) -> str:
        profile = state["profile"]
        image_url = state["avatar"]["url"] or state["photo"]["url"]
        name = escape(str(profile.get("full_name") or "Tu nombre"))
        age = escape(str(profile.get("age") or "—"))
        department = escape(str(profile.get("department") or "Neurotry"))
        description = escape(str(profile.get("short_description") or "Construyendo el futuro"))
        image = escape(str(image_url or ""), quote=True)
        return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tarjeta de {name}</title>
<style>
@page{{size:A6 landscape;margin:0}}*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#07152e;color:#f7fbff;font-family:Georgia,serif}}
.sheet{{width:148mm;height:105mm;padding:12mm;display:grid;grid-template-columns:44mm 1fr;gap:10mm;align-items:center;position:relative;overflow:hidden;background:radial-gradient(circle at 10% 10%,#0c75ff 0,transparent 38%),linear-gradient(135deg,#061329,#0a2858 58%,#075bd1)}}
.sheet:after{{content:"";position:absolute;inset:5mm;border:1px solid #74c8ff55;border-radius:5mm;pointer-events:none}}.portrait{{width:44mm;height:56mm;object-fit:cover;border-radius:22mm 22mm 9mm 9mm;border:1.2mm solid #a8dcff;box-shadow:0 0 12mm #23a7ff99;background:#123}}
.brand{{font:700 7mm/1 sans-serif;letter-spacing:.8mm;text-transform:uppercase;color:#80d5ff}}h1{{font-size:9mm;line-height:1;margin:6mm 0 3mm;max-width:72mm}}.dept{{font:700 4mm/1.2 sans-serif;text-transform:uppercase;letter-spacing:.4mm;color:#a5e2ff}}.bio{{font-size:4.5mm;line-height:1.35;margin-top:5mm}}.meta{{font:3.3mm sans-serif;color:#b8cee9;margin-top:4mm}}
.actions{{position:fixed;right:20px;top:20px;display:flex;gap:8px}}button{{border:0;border-radius:999px;padding:12px 18px;background:#1598ff;color:white;font-weight:700;cursor:pointer}}@media print{{body{{min-height:0}}.actions{{display:none}}}}
</style></head><body>
<main class="sheet"><img class="portrait" src="{image}" alt="Avatar corporativo de {name}"><section><div class="brand">Neurotry</div><h1>{name}</h1><div class="dept">{department}</div><p class="bio">{description}</p><p class="meta">{age} años · Miembro del equipo</p></section></main>
<div class="actions"><button onclick="window.print()">Guardar como PDF</button></div>
<script>addEventListener('load',()=>setTimeout(()=>window.print(),300))</script></body></html>"""
