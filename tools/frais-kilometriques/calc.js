// Barème fiscal voitures : [taux jusqu'à 5 000 km], [taux, fixe de 5 001 à 20 000 km], [taux au-delà de 20 000 km]
var BAREME = {
  3: [0.529, 0.316, 1065, 0.370],
  4: [0.606, 0.340, 1330, 0.407],
  5: [0.636, 0.357, 1395, 0.427],
  6: [0.665, 0.374, 1457, 0.447],
  7: [0.697, 0.394, 1515, 0.470]
};
CM.live(function () {
  var b = BAREME[CM.val("cv")];
  var d = CM.num("km");
  var total, formule;
  if (d <= 5000) { total = d * b[0]; formule = "d × " + b[0]; }
  else if (d <= 20000) { total = d * b[1] + b[2]; formule = "(d × " + b[1] + ") + " + b[2]; }
  else { total = d * b[3]; formule = "d × " + b[3]; }
  if (document.getElementById("elec").checked) { total *= 1.2; formule += " × 1,2"; }
  CM.set("r-total", CM.euro(total, 0));
  CM.set("r-formule", formule.replace(/\./g, ","));
  CM.set("r-km", d > 0 ? CM.euro(total / d, 3) : "–");
});
