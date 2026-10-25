// Teste un calculateur sans navigateur : faux DOM minimal, exécution du JS,
// et vérification que les résultats affichés ne contiennent ni NaN ni Infinity.
// Usage : node scripts/check_tool.js tools/<slug>
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const dir = process.argv[2];
const html = fs.readFileSync(path.join(dir, "calc.html"), "utf8");
const js = fs.readFileSync(path.join(dir, "calc.js"), "utf8");
const app = fs.readFileSync(path.join(__dirname, "..", "assets", "app.js"), "utf8");

function fail(msg) {
  console.error("ÉCHEC : " + msg);
  process.exit(1);
}

// Récupère chaque élément ayant un id, avec une valeur par défaut plausible.
const elements = {};
const tagRe = /<(input|select|textarea|div|span|td|p|strong|output|b|li|th)\b([^>]*)>/gi;
let m;
while ((m = tagRe.exec(html))) {
  const tag = m[1].toLowerCase();
  const attrs = m[2];
  const id = (attrs.match(/\bid="([^"]+)"/) || [])[1];
  if (!id) continue;
  if (elements[id]) fail(`id en double : ${id}`);
  let value = (attrs.match(/\bvalue="([^"]*)"/) || [])[1] || "";
  if (tag === "select") {
    const rest = html.slice(m.index);
    const block = rest.slice(0, rest.indexOf("</select>"));
    const sel = block.match(/<option[^>]*\bselected\b[^>]*value="([^"]*)"/) ||
      block.match(/<option[^>]*value="([^"]*)"[^>]*\bselected\b/) ||
      block.match(/<option[^>]*value="([^"]*)"/);
    if (!sel) fail(`select sans option : ${id}`);
    value = sel[1];
  }
  const checked = /\bchecked\b/.test(attrs);
  elements[id] = { id, tagName: tag.toUpperCase(), value, checked, textContent: "", innerHTML: "",
    style: {}, classList: { add() {}, remove() {}, toggle() {} },
    addEventListener() {}, setAttribute() {}, removeAttribute() {} };
}

const used = new Set();
const handlers = [];
const document = {
  getElementById(id) {
    used.add(id);
    if (!(id in elements) && id !== "calc" && id !== "search") fail(`id introuvable dans calc.html : ${id}`);
    if (id === "calc") return { addEventListener() {} };
    return elements[id] || null;
  },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener(ev, fn) { if (ev === "DOMContentLoaded") handlers.push(fn); },
  createElement() { return { style: {}, appendChild() {}, setAttribute() {} }; },
};
const errors = [];
const sandbox = { document, console: { log() {}, error: (e) => errors.push(String(e)), warn() {} },
  Math, Number, parseFloat, parseInt, isNaN, isFinite, String, Date, JSON, Array, Object };
sandbox.window = sandbox;
vm.createContext(sandbox);
try {
  vm.runInContext(app, sandbox, { timeout: 2000 });
  vm.runInContext(`(function(){\n${js}\n})();`, sandbox, { timeout: 2000 });
  handlers.forEach((h) => h());
} catch (e) {
  fail("erreur d'exécution : " + e.message);
}
if (errors.length) fail("erreur dans le calcul : " + errors[0]);
const outputs = Object.values(elements).filter((e) => e.textContent || e.innerHTML);
if (!outputs.length) fail("aucun résultat n'est affiché avec les valeurs par défaut");
for (const e of outputs) {
  const t = e.textContent + e.innerHTML;
  if (/NaN|Infinity|undefined/.test(t)) fail(`résultat invalide dans #${e.id} : ${t}`);
}
console.log(`OK : ${outputs.length} résultats affichés`);
