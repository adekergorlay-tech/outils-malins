# Calculs Malins

Site de calculateurs gratuits sur l'argent du quotidien, **hébergé gratuitement sur GitHub Pages** et **enrichi automatiquement** : deux fois par semaine, un robot (GitHub Actions + Google Gemini, version gratuite) crée un nouveau calculateur, le teste et le publie.

## Fonctionnement

| Élément | Rôle |
|---|---|
| `tools/<slug>/` | Un dossier par calculateur : `meta.json`, `calc.html`, `calc.js`, `guide.html` |
| `tools/backlog.json` | La file d'idées à publier. Quand elle est vide, Gemini en propose de nouvelles |
| `scripts/generate.py` | Le robot : demande un calculateur à Gemini, le vérifie, l'ajoute |
| `scripts/check_tool.js` | Teste chaque calculateur (pas d'erreur, pas de NaN) avant publication |
| `scripts/build.py` | Construit le site (pages, sitemap, robots.txt, ads.txt) dans `_site/` |
| `.github/workflows/site.yml` | Lance tout : à chaque modification, et le lundi et le jeudi à 6 h UTC |
| `config.json` | Nom du site, catégories, codes AdSense / GoatCounter, blocs d'affiliation |

## Réglages à faire une seule fois

1. **Activer GitHub Pages** : Settings → Pages → Source : **GitHub Actions**.
2. **Clé Gemini** : créer une clé gratuite sur https://aistudio.google.com/apikey, puis Settings → Secrets and variables → Actions → New repository secret, nom `GEMINI_API_KEY`.
3. Facultatif : publier un outil tout de suite avec Actions → « Générer et publier le site » → Run workflow.

## Monétisation (plus tard)

- **Google AdSense** : une fois le site lancé avec du trafic, mettre l'identifiant `ca-pub-…` dans `adsense_client` de `config.json`. Les emplacements de pub et `ads.txt` se créent automatiquement.
- **Affiliation** : dans `affiliate_blocks`, associer à une catégorie un bloc HTML (par exemple une offre de courtier pour `immobilier`).
- **Statistiques gratuites** : créer un compte sur goatcounter.com et mettre son code dans `goatcounter_code`.

## Tester en local

```
python3 scripts/build.py && cd _site && python3 -m http.server
```
