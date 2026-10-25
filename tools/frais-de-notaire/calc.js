CM.live(function () {
  var p = CM.num("prix");
  var mob = CM.num("mobilier");
  var type = CM.val("type_bien");
  var dep = CM.val("departement");

  if (p <= 0) {
    CM.set("r-total", "0 €");
    CM.set("r-taxes", "0 €");
    CM.set("r-emoluments", "0 €");
    CM.set("r-debours", "0 €");
    CM.set("r-csi", "0 €");
    CM.set("r-pourcent", "0,0 %");
    return;
  }

  var assietteDroits = Math.max(0, p - mob);
  var taxes = 0;
  var csi = Math.max(15, Math.round(assietteDroits * 0.0010));
  var debours = type === "neuf" ? 900 : 1200;

  if (type === "ancien") {
    var tauxDep = (dep === "reduit") ? 0.038 : 0.045;
    var comm = 0.012;
    var fraisColl = tauxDep * 0.0237;
    var tauxDMTO = tauxDep + comm + fraisColl;
    taxes = assietteDroits * tauxDMTO;
  } else {
    taxes = assietteDroits * 0.00715;
  }

  var emHT = 0;
  var t1 = Math.min(p, 6500);
  emHT += t1 * 0.03870;
  if (p > 6500) {
    var t2 = Math.min(p, 17000) - 6500;
    emHT += t2 * 0.01596;
  }
  if (p > 17000) {
    var t3 = Math.min(p, 60000) - 17000;
    emHT += t3 * 0.01064;
  }
  if (p > 60000) {
    var t4 = p - 60000;
    emHT += t4 * 0.00799;
  }

  var emolumentsTTC = emHT * 1.20;
  var total = taxes + emolumentsTTC + debours + csi;

  CM.set("r-total", CM.euro(total, 0));
  CM.set("r-taxes", CM.euro(taxes, 0));
  CM.set("r-emoluments", CM.euro(emolumentsTTC, 0));
  CM.set("r-debours", CM.euro(debours, 0));
  CM.set("r-csi", CM.euro(csi, 0));
  CM.set("r-pourcent", CM.nb((total / p) * 100, 2) + " %");
});
