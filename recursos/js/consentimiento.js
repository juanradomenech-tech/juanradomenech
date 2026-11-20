/* juanradomenech.com · aviso de cookies y Google Analytics (solo se carga si aceptas) */
(function () {
  "use strict";
  var ID = document.documentElement.getAttribute("data-ga");
  if (!ID) return;
  var CLAVE = "jd_cookies";

  function leer() { try { return localStorage.getItem(CLAVE); } catch (e) { return null; } }
  function guardar(v) { try { localStorage.setItem(CLAVE, v); } catch (e) {} }

  var cargado = false;
  function cargarGA() {
    if (cargado) return;
    cargado = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    var s = document.createElement("script");
    s.async = true;
    if (ID.indexOf("GTM-") === 0) {
      /* Contenedor de Google Tag Manager (lleva Analytics dentro) */
      window.dataLayer.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
      s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(ID);
    } else {
      /* ID de medición de Google Analytics 4 (G-...) */
      window.gtag("config", ID);
      s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(ID);
    }
    document.head.appendChild(s);
  }

  function borrarCookiesGA() {
    var dominios = [location.hostname, "." + location.hostname.replace(/^www\./, "")];
    document.cookie.split(";").forEach(function (c) {
      var nombre = c.split("=")[0].trim();
      if (nombre.indexOf("_ga") === 0) {
        dominios.forEach(function (d) {
          document.cookie = nombre + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=" + d;
        });
        document.cookie = nombre + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
      }
    });
  }

  var barra = null;
  function mostrar() {
    if (barra) { barra.hidden = false; return; }
    barra = document.createElement("div");
    barra.className = "aviso-cookies";
    barra.setAttribute("role", "dialog");
    barra.setAttribute("aria-label", "Aviso de cookies");
    barra.innerHTML =
      '<p>Uso cookies de Google Analytics para saber cuántas personas visitan la web y qué páginas leen. Solo se activan si las aceptas. ' +
      '<a href="/cookies.html">Más información</a>.</p>' +
      '<div class="aviso-cookies-botones">' +
      '<button type="button" class="boton boton--linea" data-rechazar>Rechazar</button>' +
      '<button type="button" class="boton" data-aceptar>Aceptar</button></div>';
    document.body.appendChild(barra);
    barra.querySelector("[data-aceptar]").addEventListener("click", function () {
      guardar("si"); barra.hidden = true; cargarGA();
    });
    barra.querySelector("[data-rechazar]").addEventListener("click", function () {
      guardar("no"); barra.hidden = true; borrarCookiesGA();
      if (cargado) location.reload();
    });
  }

  document.querySelectorAll("[data-cookies]").forEach(function (b) {
    b.hidden = false;
    b.addEventListener("click", mostrar);
  });

  var eleccion = leer();
  if (eleccion === "si") cargarGA();
  else if (eleccion !== "no") mostrar();
})();
