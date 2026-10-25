CM.live(function () {
  var m = CM.num("montant");
  var t = parseFloat(CM.val("taux")) / 100;
  var ht = CM.val("sens") === "ht" ? m : m / (1 + t);
  CM.set("r-ht", CM.euro(ht));
  CM.set("r-tva", CM.euro(ht * t));
  CM.set("r-ttc", CM.euro(ht * (1 + t)));
});
