CM.live(function () {
  var c = CM.num("capital");
  var n = Math.round(CM.num("duree") * 12);
  var t = CM.num("taux") / 100 / 12;
  if (c <= 0 || n <= 0) return;
  var hors = t > 0 ? c * t / (1 - Math.pow(1 + t, -n)) : c / n;
  var ass = c * CM.num("assurance") / 100 / 12;
  var mens = hors + ass;
  CM.set("r-mens", CM.euro(mens));
  CM.set("r-hors", CM.euro(hors));
  CM.set("r-ass", CM.euro(ass));
  CM.set("r-int", CM.euro(hors * n - c, 0));
  CM.set("r-ass-tot", CM.euro(ass * n, 0));
  var rev = CM.num("revenus");
  CM.set("r-endet", rev > 0 ? CM.nb(mens / rev * 100, 1) + " %" + (mens / rev > 0.35 ? " (au-dessus de 35 %)" : "") : "–");
});
