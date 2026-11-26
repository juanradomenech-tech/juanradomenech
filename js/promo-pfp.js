/* juanradomenech.com · ventana de Black Friday de Personal Finance PRO
   Sale al entrar (cuando ya no está el aviso de cookies), una vez por visita y, si se cierra, no vuelve en 2 días.
   Desaparece sola al terminar la promoción. */
(function () {
  "use strict";
  var FIN = new Date("2026-11-30T23:59:59+01:00").getTime();
  var CLAVE = "jd_promo_pfp_bf";
  var APP = "https://app.juanradomenech.com";
  if (Date.now() > FIN) return;
  var ruta = location.pathname;
  if (/personalfinance|condiciones|privacidad|aviso-legal|cookies/.test(ruta)) return;
  try {
    if (sessionStorage.getItem(CLAVE)) return;
    var hasta = parseInt(localStorage.getItem(CLAVE) || "0", 10);
    if (hasta && Date.now() < hasta) return;
  } catch (e) {}

  function marcar(dias) {
    try {
      sessionStorage.setItem(CLAVE, "1");
      if (dias) localStorage.setItem(CLAVE, String(Date.now() + dias * 864e5));
    } catch (e) {}
  }

  function crear() {
    var v = document.createElement("div");
    v.className = "promo-pfp";
    v.setAttribute("role", "dialog");
    v.setAttribute("aria-modal", "true");
    v.setAttribute("aria-labelledby", "promo-pfp-titulo");
    v.innerHTML =
      '<div class="promo-pfp-caja">' +
        '<button class="promo-pfp-cerrar" type="button" aria-label="Cerrar">&times;</button>' +
        '<p class="promo-pfp-marca"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="1" y="1" width="22" height="22" rx="11" fill="#000"/><rect x="6" y="13" width="3" height="5" rx="1" fill="#fff"/><rect x="10.5" y="9" width="3" height="9" rx="1" fill="#fff"/><rect x="15" y="6" width="3" height="12" rx="1" fill="#FF671F"/></svg><span><b>Personal Finance</b> Pro</span></p>' +
        '<h2 id="promo-pfp-titulo">¿Sabes cuánto te gastas al año en atún? ¿Y en cerveza?...</h2>' +
        '<p class="promo-pfp-texto">Apunta cada gasto escribiendo, dictando o con una foto del ticket. La IA lo coloca en su partida y ves tu presupuesto semana a semana.</p>' +
        '<p class="promo-pfp-banda">Precio Black Friday: −20&nbsp;% para siempre · hasta el 30 de noviembre</p>' +
        '<div class="promo-pfp-planes">' +
          '<div class="promo-pfp-plan"><span class="promo-pfp-tipo">Mensual</span><s>1,99 €</s><strong>1,59 €<small>/mes</small></strong></div>' +
          '<div class="promo-pfp-plan promo-pfp-plan--top"><span class="promo-pfp-tipo">Anual</span><s>19,99 €</s><strong>15,99 €<small>/año</small></strong><em>2 meses gratis</em></div>' +
        '</div>' +
        '<a class="promo-pfp-boton" href="' + APP + '">Empieza gratis</a>' +
        '<p class="promo-pfp-nota">Plan gratis con 100 créditos de IA. PRO con 14 días gratis; cancela cuando quieras.</p>' +
        '<a class="promo-pfp-mas" href="/personalfinance.html">Ver cómo funciona</a>' +
      '</div>';
    document.body.appendChild(v);
    document.documentElement.classList.add("promo-pfp-abierta");
    requestAnimationFrame(function () { v.classList.add("visible"); });

    function cerrar() {
      marcar(2);
      v.classList.remove("visible");
      document.documentElement.classList.remove("promo-pfp-abierta");
      document.removeEventListener("keydown", tecla);
      setTimeout(function () { v.remove(); }, 300);
    }
    function tecla(e) { if (e.key === "Escape") cerrar(); }
    v.querySelector(".promo-pfp-cerrar").addEventListener("click", cerrar);
    v.addEventListener("click", function (e) { if (e.target === v) cerrar(); });
    document.addEventListener("keydown", tecla);
    v.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", function () { marcar(7); }); });
    marcar(0);
    v.querySelector(".promo-pfp-boton").focus({ preventScroll: true });
  }

  // Espera a que el visitante haya visto un poco la página y a que no esté el aviso de cookies
  var empezar = Date.now();
  function cookiesVisibles() {
    var b = document.querySelector(".aviso-cookies");
    return !!b && !b.hidden && getComputedStyle(b).display !== "none" && getComputedStyle(b).visibility !== "hidden";
  }
  (function esperar() {
    var t = Date.now() - empezar;
    // Espera 2,5 s; si sigue el aviso de cookies sin responder, sale igualmente a los 8 s
    if (t < 2500 || (cookiesVisibles() && t < 8000)) { setTimeout(esperar, 500); return; }
    crear();
  })();
})();
