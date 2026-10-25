#!/usr/bin/env python3
"""Construit le site statique dans _site/ à partir de tools/*/ et de config.json."""
import html
import json
import os
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "_site"


def load_config():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    cfg["site_url"] = os.environ.get("SITE_URL", cfg.get("site_url", "")).rstrip("/")
    base = os.environ.get("BASE_PATH", cfg.get("base_path", "")).strip("/")
    cfg["base_path"] = f"/{base}/" if base else "/"
    return cfg


def load_tools():
    tools = []
    for meta_file in sorted(TOOLS.glob("*/meta.json")):
        d = meta_file.parent
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["slug"] = d.name
        meta["calc_html"] = (d / "calc.html").read_text(encoding="utf-8")
        meta["calc_js"] = (d / "calc.js").read_text(encoding="utf-8")
        meta["guide_html"] = (d / "guide.html").read_text(encoding="utf-8")
        tools.append(meta)
    tools.sort(key=lambda t: t.get("date", ""), reverse=True)
    return tools


def esc(s):
    return html.escape(str(s), quote=True)


def layout(cfg, *, title, description, path, body, extra_head=""):
    b = cfg["base_path"]
    canonical = f'{cfg["site_url"]}{b}{path}' if cfg["site_url"] else ""
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<link rel="stylesheet" href="{b}assets/style.css">',
        f'<link rel="icon" href="{b}assets/favicon.svg" type="image/svg+xml">',
        f'<script src="{b}assets/app.js"></script>',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        '<meta property="og:type" content="website">',
    ]
    if canonical:
        head.append(f'<link rel="canonical" href="{esc(canonical)}">')
        head.append(f'<meta property="og:url" content="{esc(canonical)}">')
    if cfg.get("google_site_verification"):
        head.append(f'<meta name="google-site-verification" content="{esc(cfg["google_site_verification"])}">')
    if cfg.get("adsense_client"):
        head.append(
            '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
            f'?client={esc(cfg["adsense_client"])}" crossorigin="anonymous"></script>'
        )
    if cfg.get("goatcounter_code"):
        head.append(
            f'<script data-goatcounter="https://{esc(cfg["goatcounter_code"])}.goatcounter.com/count" '
            'async src="//gc.zgo.at/count.js"></script>'
        )
    year = date.today().year
    return f"""<!doctype html>
<html lang="{cfg['lang']}">
<head>
{chr(10).join(head)}
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{b}"><span class="logo">€</span> {esc(cfg['site_name'])}</a>
    <nav><a href="{b}#outils">Tous les outils</a></nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>© {year} {esc(cfg['site_name'])} · Les résultats sont des estimations indicatives et ne remplacent pas l'avis d'un professionnel.</p>
    <p><a href="{b}mentions-legales/">Mentions légales</a> · <a href="{b}confidentialite/">Confidentialité</a></p>
  </div>
</footer>
</body>
</html>
"""


def ad_slot(cfg):
    if not cfg.get("adsense_client"):
        return ""
    return (
        '<div class="ad"><ins class="adsbygoogle" style="display:block" '
        f'data-ad-client="{esc(cfg["adsense_client"])}" data-ad-format="auto" '
        'data-full-width-responsive="true"></ins>'
        "<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>"
    )


def tool_card(cfg, t):
    return (
        f'<a class="card" href="{cfg["base_path"]}outils/{t["slug"]}/">'
        f'<span class="card-emoji">{esc(t.get("emoji", "🧮"))}</span>'
        f'<strong>{esc(t["title"])}</strong><span>{esc(t["description"])}</span></a>'
    )


def render_tool(cfg, t, tools):
    related = [x for x in tools if x["category"] == t["category"] and x["slug"] != t["slug"]][:4]
    if len(related) < 4:
        related += [x for x in tools if x["slug"] != t["slug"] and x not in related][: 4 - len(related)]
    faq = t.get("faq", [])
    faq_html = "".join(
        f"<details><summary>{esc(q['q'])}</summary><p>{esc(q['a'])}</p></details>" for q in faq
    )
    ld = [{
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": t["title"],
        "description": t["description"],
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "Tous",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
    }]
    if faq:
        ld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                for q in faq
            ],
        })
    extra_head = "".join(
        f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld
    )
    affiliate = cfg.get("affiliate_blocks", {}).get(t["category"], "")
    cat = cfg["categories"].get(t["category"], t["category"])
    body = f"""
<nav class="crumbs"><a href="{cfg['base_path']}">Accueil</a> › {esc(cat)}</nav>
<h1>{esc(t.get('emoji', '🧮'))} {esc(t['title'])}</h1>
<p class="lead">{esc(t['description'])}</p>
<section class="calc" id="calc">
{t['calc_html']}
</section>
{ad_slot(cfg)}
<article class="guide">
{t['guide_html']}
</article>
{f'<aside class="affiliate">{affiliate}</aside>' if affiliate else ''}
{f'<section class="faq"><h2>Questions fréquentes</h2>{faq_html}</section>' if faq else ''}
<section class="related"><h2>Autres outils utiles</h2><div class="grid">{''.join(tool_card(cfg, x) for x in related)}</div></section>
<p class="updated">Mis à jour le {esc(t.get('date', ''))}</p>
<script>
(function(){{
{t['calc_js']}
}})();
</script>
"""
    return layout(cfg, title=f"{t['title']} – {cfg['site_name']}", description=t["description"],
                  path=f"outils/{t['slug']}/", body=body, extra_head=extra_head)


def render_index(cfg, tools):
    sections = []
    for key, label in cfg["categories"].items():
        items = [t for t in tools if t["category"] == key]
        if items:
            sections.append(
                f'<section><h2>{esc(label)}</h2><div class="grid">{"".join(tool_card(cfg, t) for t in items)}</div></section>'
            )
    latest = "".join(tool_card(cfg, t) for t in tools[:3])
    body = f"""
<section class="hero">
  <h1>{esc(cfg['tagline'])}</h1>
  <p>{esc(cfg['description'])}</p>
  <input id="search" type="search" placeholder="Rechercher un calculateur…" aria-label="Rechercher">
</section>
<section><h2>Nouveautés</h2><div class="grid">{latest}</div></section>
<div id="outils">{''.join(sections)}</div>
"""
    return layout(cfg, title=f"{cfg['site_name']} – {cfg['tagline']}", description=cfg["description"],
                  path="", body=body)


def render_page(cfg, slug, title, inner):
    return layout(cfg, title=f"{title} – {cfg['site_name']}", description=title, path=f"{slug}/",
                  body=f'<article class="guide"><h1>{esc(title)}</h1>{inner}</article>')


def legal_pages(cfg):
    owner = esc(cfg.get("owner_name") or "le propriétaire du site")
    contact = esc(cfg.get("contact_email") or "via la page GitHub du projet")
    mentions = f"""
<p><strong>Éditeur :</strong> {owner}, particulier. Contact : {contact}.</p>
<p><strong>Hébergement :</strong> GitHub Pages, GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis.</p>
<p>Les calculateurs fournissent des estimations à titre indicatif. Ils ne constituent ni un conseil financier, ni un conseil juridique ou fiscal.
Certains contenus sont rédigés avec l'aide d'outils d'intelligence artificielle puis publiés automatiquement.</p>
<p>Certains liens peuvent être des liens d'affiliation : le site peut percevoir une commission, sans surcoût pour vous.</p>
"""
    privacy = """
<p>Les calculs sont faits directement dans votre navigateur : les chiffres que vous saisissez ne sont ni envoyés ni stockés sur un serveur.</p>
<p>Le site peut utiliser une mesure d'audience respectueuse de la vie privée (sans cookie) et, le cas échéant, des publicités fournies par Google AdSense,
qui peut déposer des cookies. Vous pouvez gérer vos préférences publicitaires sur <a href="https://adssettings.google.com">adssettings.google.com</a>.</p>
"""
    return {
        "mentions-legales": ("Mentions légales", mentions),
        "confidentialite": ("Politique de confidentialité", privacy),
    }


def main():
    cfg = load_config()
    tools = load_tools()
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    # Fichiers à placer tels quels à la racine (vérification Google, etc.)
    if (ROOT / "static").exists():
        shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
    (OUT / "index.html").write_text(render_index(cfg, tools), encoding="utf-8")
    for t in tools:
        p = OUT / "outils" / t["slug"]
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(render_tool(cfg, t, tools), encoding="utf-8")
    for slug, (title, inner) in legal_pages(cfg).items():
        p = OUT / slug
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(render_page(cfg, slug, title, inner), encoding="utf-8")
    (OUT / "404.html").write_text(
        render_page(cfg, "404", "Page introuvable", f'<p><a href="{cfg["base_path"]}">Retour à l\'accueil</a></p>'),
        encoding="utf-8",
    )
    # Index de recherche pour la barre de l'accueil
    (OUT / "assets" / "search.json").write_text(json.dumps(
        [{"t": t["title"], "d": t["description"], "u": f'{cfg["base_path"]}outils/{t["slug"]}/'} for t in tools],
        ensure_ascii=False), encoding="utf-8")
    if cfg["site_url"]:
        base = cfg["site_url"] + cfg["base_path"]
        urls = [(base, date.today().isoformat())] + [
            (f"{base}outils/{t['slug']}/", t.get("date", date.today().isoformat())) for t in tools
        ]
        sm = "".join(f"<url><loc>{esc(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
        (OUT / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>',
            encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n", encoding="utf-8")
    if cfg.get("adsense_client"):
        pub = cfg["adsense_client"].replace("ca-", "")
        (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Site construit : {len(tools)} outils -> {OUT}")


if __name__ == "__main__":
    main()
