CM.live(function () {
  var brut = CM.num("brut");
  var mensuel = CM.val("periode") === "an" ? brut / 12 : brut;
  var taux = parseFloat(CM.val("statut"));
  var net = mensuel * (1 - taux);
  var pas = CM.num("pas") / 100;
  CM.set("r-net", CM.euro(net));
  CM.set("r-net-an", CM.euro(net * 12, 0));
  CM.set("r-net-pas", CM.euro(net * (1 - pas)));
  CM.set("r-cotis", CM.euro(mensuel - net));
});
