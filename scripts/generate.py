#!/usr/bin/env python3
"""Robot de publication : crée un nouveau calculateur avec Gemini à partir de tools/backlog.json.

Variables d'environnement :
  GEMINI_API_KEY  clé gratuite créée sur https://aistudio.google.com/apikey (obligatoire)
  GEMINI_MODEL    modèle à utiliser (facultatif)
  COUNT           nombre d'outils à créer pendant ce passage (défaut : 1)
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
BACKLOG = TOOLS / "backlog.json"
MODELS = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-2.5-flash", "gemini-2.0-flash"] if m]
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

FORBIDDEN_JS = ["fetch(", "XMLHttpRequest", "eval(", "Function(", "import(", "document.write",
                "<script", "localStorage", "sessionStorage", "document.cookie", "window.location",
                "setInterval"]
FORBIDDEN_HTML = re.compile(r"<script|<iframe|<object|<embed|<style|<link|\son\w+\s*=|javascript:", re.I)


def gemini(prompt, schema=None):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY manquante : ajoutez-la dans Settings > Secrets and variables > Actions.")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
    }
    if schema:
        body["generationConfig"]["responseSchema"] = schema
    last = None
    for model in MODELS:
        for attempt in range(3):
            req = urllib.request.Request(
                API.format(model=model), data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "x-goog-api-key": key})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.load(r)
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except urllib.error.HTTPError as e:
                last = f"{model}: HTTP {e.code} {e.read()[:300]!r}"
                if e.code == 404:
                    break  # modèle indisponible : on passe au suivant
                time.sleep(20 * (attempt + 1))
            except (KeyError, IndexError, json.JSONDecodeError, urllib.error.URLError) as e:
                last = f"{model}: {e}"
                time.sleep(5)
    raise RuntimeError(f"Gemini n'a pas répondu correctement ({last})")


TOOL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "emoji": {"type": "STRING"},
        "calc_html": {"type": "STRING"},
        "calc_js": {"type": "STRING"},
        "guide_html": {"type": "STRING"},
        "faq": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "q": {"type": "STRING"}, "a": {"type": "STRING"}}, "required": ["q", "a"]}},
    },
    "required": ["title", "description", "emoji", "calc_html", "calc_js", "guide_html", "faq"],
}


def tool_prompt(item, example, feedback):
    return f"""Tu es développeur web et rédacteur expert en finances personnelles françaises.
Crée une page de calculateur gratuit pour le site français "Calculs Malins".

Sujet : {item['title']}
Slug : {item['slug']}
Notes : {item.get('notes', '')}

Contraintes techniques STRICTES :
- calc_html : uniquement du HTML (pas de <script>, pas de style inline sauf style="width:auto" sur une case à cocher, pas d'attribut onclick/oninput).
  Utilise les classes existantes : <div class="row"> pour mettre 2 champs côte à côte, <label for>, <input type="text" inputmode="decimal" value="..."> pour les nombres,
  <select>, <span class="hint"> pour une aide, et un bloc <div class="result"> avec <div class="big" id="..."> pour le résultat principal et un <table> de résultats détaillés.
  Chaque champ a une valeur par défaut réaliste pour qu'un résultat s'affiche dès le chargement.
- calc_js : JavaScript ES5 sans dépendance, qui utilise uniquement l'objet global CM :
  CM.live(fn) relance fn à chaque saisie ; CM.num(id) lit un nombre ; CM.val(id) lit une valeur texte ; CM.set(id, texte) écrit un résultat ;
  CM.euro(n, decimales) formate en euros ; CM.nb(n, decimales) formate un nombre. Pas de fetch, eval, localStorage ni accès réseau.
  Gère les cas limites (division par zéro, champ vide) sans jamais afficher NaN ou Infinity.
- guide_html : 400 à 700 mots en HTML (h2, p, ul, table), sans h1. Explique la méthode de calcul, donne un exemple chiffré, des conseils pratiques.
  Les règles et montants doivent être exacts pour la France. Si un chiffre officiel change chaque année (plafond, barème, taux),
  indique qu'il faut vérifier la valeur en vigueur sur le site officiel (service-public.fr, impots.gouv.fr, urssaf.fr…). N'invente aucun chiffre.
- faq : 3 à 5 questions-réponses courtes que les gens tapent vraiment sur Google.
- title : titre SEO de moins de 60 caractères. description : phrase de 120 à 155 caractères. emoji : un seul emoji.

Voici un exemple de calculateur existant à imiter pour le style et la structure :
calc_html :
{example['calc_html']}
calc_js :
{example['calc_js']}
{f"ATTENTION, ta tentative précédente a été refusée pour cette raison : {feedback}. Corrige ce problème." if feedback else ""}
Réponds uniquement avec l'objet JSON demandé."""


def validate(res):
    for word in FORBIDDEN_JS:
        if word in res["calc_js"]:
            return f"calc_js contient une instruction interdite : {word}"
    for field in ("calc_html", "guide_html"):
        bad = FORBIDDEN_HTML.search(res[field].replace('style="width:auto"', ""))
        if bad:
            return f"{field} contient du code interdit : {bad.group(0)}"
    if "<h1" in res["guide_html"].lower():
        return "guide_html ne doit pas contenir de h1"
    if len(re.sub(r"<[^>]+>", " ", res["guide_html"]).split()) < 250:
        return "guide_html est trop court (au moins 400 mots demandés)"
    if not 3 <= len(res["faq"]) <= 6:
        return "la faq doit contenir 3 à 5 questions"
    if "CM.live" not in res["calc_js"]:
        return "calc_js doit utiliser CM.live(...)"
    return None


def write_tool(item, res):
    d = TOOLS / item["slug"]
    d.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": res["title"].strip(),
        "description": res["description"].strip(),
        "category": item["category"],
        "emoji": res["emoji"].strip()[:4] or "🧮",
        "date": date.today().isoformat(),
        "generated": True,
        "faq": res["faq"],
    }
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (d / "calc.html").write_text(res["calc_html"].strip() + "\n", encoding="utf-8")
    (d / "calc.js").write_text(res["calc_js"].strip() + "\n", encoding="utf-8")
    (d / "guide.html").write_text(res["guide_html"].strip() + "\n", encoding="utf-8")
    return d


def run_check(d):
    r = subprocess.run(["node", str(ROOT / "scripts" / "check_tool.js"), str(d)],
                       capture_output=True, text=True)
    return None if r.returncode == 0 else (r.stderr or r.stdout).strip()


def refill_backlog(backlog, config):
    """Quand la liste d'idées est vide, Gemini en propose de nouvelles."""
    existing = sorted(p.name for p in TOOLS.iterdir() if p.is_dir())
    prompt = f"""Propose 15 nouveaux calculateurs ou simulateurs en ligne utiles pour des Français,
très recherchés sur Google, sur des sujets d'argent du quotidien. Ils doivent pouvoir fonctionner uniquement avec des formules (pas de base de données).
Catégories autorisées : {json.dumps(config['categories'], ensure_ascii=False)}.
Outils déjà publiés (à ne pas répéter) : {', '.join(existing)}.
Pour chacun : slug (minuscules, tirets, sans accent), title, category (une clé autorisée), notes (formule ou règle à appliquer)."""
    schema = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "slug": {"type": "STRING"}, "title": {"type": "STRING"},
        "category": {"type": "STRING"}, "notes": {"type": "STRING"}},
        "required": ["slug", "title", "category", "notes"]}}
    ideas = gemini(prompt, schema)
    for i in ideas:
        i["slug"] = re.sub(r"[^a-z0-9-]", "", i["slug"].lower())[:60]
        if i["slug"] and i["slug"] not in existing and i["category"] in config["categories"]:
            backlog.append(i)
    print(f"Backlog rechargé : {len(backlog)} idées")


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
    ex_dir = TOOLS / "mensualite-pret-immobilier"
    example = {"calc_html": (ex_dir / "calc.html").read_text(encoding="utf-8"),
               "calc_js": (ex_dir / "calc.js").read_text(encoding="utf-8")}
    created = 0
    for _ in range(int(os.environ.get("COUNT", "1"))):
        if not backlog:
            refill_backlog(backlog, config)
        while backlog:
            item = backlog.pop(0)
            if (TOOLS / item["slug"]).exists() or item["category"] not in config["categories"]:
                continue
            feedback = None
            for attempt in range(3):
                print(f"→ {item['title']} (essai {attempt + 1})")
                try:
                    res = gemini(tool_prompt(item, example, feedback), TOOL_SCHEMA)
                except RuntimeError as e:
                    print(e)
                    sys.exit(1)
                feedback = validate(res)
                if feedback:
                    print("  refusé :", feedback)
                    continue
                d = write_tool(item, res)
                feedback = run_check(d)
                if feedback:
                    print("  refusé :", feedback)
                    for f in d.iterdir():
                        f.unlink()
                    d.rmdir()
                    continue
                print(f"  publié : tools/{item['slug']}")
                created += 1
                break
            else:
                print(f"  abandonné après 3 essais : {item['slug']}")
                item["failed"] = item.get("failed", 0) + 1
                if item["failed"] < 2:
                    backlog.append(item)  # on retentera plus tard
                continue
            break
    BACKLOG.write_text(json.dumps(backlog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{created} outil(s) créé(s)")


if __name__ == "__main__":
    main()
