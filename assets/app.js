// Fonctions partagées par tous les calculateurs (objet global CM).
window.CM = {
  // Lit un champ numérique (accepte la virgule française). Renvoie 0 si vide.
  num: function (id) {
    var el = document.getElementById(id);
    if (!el) return 0;
    var v = parseFloat(String(el.value).replace(/\s/g, "").replace(",", "."));
    return isNaN(v) ? 0 : v;
  },
  val: function (id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
  },
  euro: function (n, dec) {
    return Number(n).toLocaleString("fr-FR", {
      style: "currency", currency: "EUR",
      minimumFractionDigits: dec === undefined ? 2 : dec,
      maximumFractionDigits: dec === undefined ? 2 : dec
    });
  },
  nb: function (n, dec) {
    return Number(n).toLocaleString("fr-FR", { maximumFractionDigits: dec === undefined ? 2 : dec });
  },
  set: function (id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  },
  // Relance fn à chaque saisie dans le bloc calculateur, et une fois au chargement.
  live: function (fn) {
    function run() { try { fn(); } catch (e) { console.error(e); } }
    document.addEventListener("DOMContentLoaded", function () {
      var root = document.getElementById("calc");
      if (root) {
        root.addEventListener("input", run);
        root.addEventListener("change", run);
      }
      run();
    });
  }
};

// Recherche sur la page d'accueil
document.addEventListener("DOMContentLoaded", function () {
  var input = document.getElementById("search");
  if (!input) return;
  input.addEventListener("input", function () {
    var q = input.value.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    document.querySelectorAll(".card").forEach(function (c) {
      var t = c.textContent.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
      c.style.display = t.indexOf(q) === -1 ? "none" : "";
    });
  });
});
