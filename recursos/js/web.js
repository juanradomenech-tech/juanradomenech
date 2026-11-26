/* juanradomenech.com · comportamiento (sin dependencias) */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js", "js-ok");

  /* Cabecera con fondo al bajar */
  var cabecera = document.querySelector(".cabecera");
  function fondo() { if (cabecera) cabecera.classList.toggle("con-fondo", window.scrollY > 40); }
  window.addEventListener("scroll", fondo, { passive: true });
  fondo();

  /* Menú móvil */
  var boton = document.querySelector(".menu-boton");
  if (boton) {
    var cerrar = function () { document.body.classList.remove("menu-abierto"); boton.setAttribute("aria-expanded", "false"); };
    boton.addEventListener("click", function () {
      var abierto = document.body.classList.toggle("menu-abierto");
      boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
    document.querySelectorAll(".menu-movil a").forEach(function (a) { a.addEventListener("click", cerrar); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") cerrar(); });
  }

  /* Menú activo según la sección visible */
  var enlaces = document.querySelectorAll(".menu a[href^='#']");
  if ("IntersectionObserver" in window && enlaces.length) {
    var mapa = {};
    enlaces.forEach(function (a) { mapa[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        if (en.isIntersecting && mapa[en.target.id]) {
          enlaces.forEach(function (a) { a.classList.remove("activo"); });
          mapa[en.target.id].classList.add("activo");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(mapa).forEach(function (id) { var s = document.getElementById(id); if (s) obs.observe(s); });
  }

  /* Aparición suave */
  var reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Fundido de cada bloque al entrar en pantalla: cada pieza (panel, título, tarjeta, foto) aparece desde negro en 1 s,
     y las piezas de una misma fila van una detrás de otra */
  document.querySelectorAll("main .panel, main .wrap > *, .pie .wrap > *").forEach(function (el) {
    if (el.classList.contains("aparece")) return;
    if (el.querySelector(".aparece")) el.classList.add("visto"); else el.classList.add("aparece");
  });
  document.querySelectorAll(".aparece").forEach(function (el) {
    var hermanos = Array.prototype.filter.call(el.parentNode.children, function (h) { return h.classList.contains("aparece"); });
    var i = hermanos.indexOf(el);
    if (hermanos.length > 1 && /^(LI|FIGURE|A|DIV)$/.test(el.tagName) && !el.parentNode.classList.contains("wrap")) el.style.transitionDelay = Math.min(i, 5) * 0.12 + "s";
  });
  document.querySelectorAll("main img").forEach(function (img) {
    var lista = function () { img.classList.add("cargada"); };
    if (img.complete && img.naturalWidth) lista(); else { img.addEventListener("load", lista); img.addEventListener("error", lista); }
  });
  var aparecen = document.querySelectorAll(".aparece");
  if (!reducir && "IntersectionObserver" in window) {
    var obs2 = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("visto"); obs2.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -10% 0px" });
    aparecen.forEach(function (el) { obs2.observe(el); });
  } else {
    aparecen.forEach(function (el) { el.classList.add("visto"); });
  }

  /* Carruseles: puntos, flechas, teclado y arrastre con ratón */
  document.querySelectorAll(".carrusel").forEach(function (car) {
    var pista = car.querySelector(".pista");
    var tarjetas = pista.querySelectorAll(".tarjeta");
    var puntos = car.querySelector(".puntos");
    var ant = car.querySelector("[data-ant]");
    var sig = car.querySelector("[data-sig]");
    if (!tarjetas.length) return;

    function paso() { return tarjetas.length > 1 ? tarjetas[1].offsetLeft - tarjetas[0].offsetLeft : pista.clientWidth; }
    function actual() { return Math.round(pista.scrollLeft / paso()); }
    function ir(i) { pista.scrollTo({ left: i * paso(), behavior: reducir ? "auto" : "smooth" }); }

    var botones = [];
    tarjetas.forEach(function (t, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Ir a " + (t.querySelector("h3") ? t.querySelector("h3").textContent : "tarjeta " + (i + 1)));
      b.addEventListener("click", function () { ir(i); });
      puntos.appendChild(b);
      botones.push(b);
    });

    function pintar() {
      var max = pista.scrollWidth - pista.clientWidth - 2;
      var i = pista.scrollLeft >= max ? tarjetas.length - 1 : actual();
      botones.forEach(function (b, j) { b.setAttribute("aria-current", j === i ? "true" : "false"); });
      if (ant) ant.disabled = pista.scrollLeft <= 2;
      if (sig) sig.disabled = pista.scrollLeft >= max;
    }
    pista.addEventListener("scroll", function () { window.requestAnimationFrame(pintar); }, { passive: true });
    window.addEventListener("resize", pintar);
    if (ant) ant.addEventListener("click", function () { ir(Math.max(0, actual() - 1)); });
    if (sig) sig.addEventListener("click", function () { ir(Math.min(tarjetas.length - 1, actual() + 1)); });
    pista.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); ir(Math.min(tarjetas.length - 1, actual() + 1)); }
      if (e.key === "ArrowLeft") { e.preventDefault(); ir(Math.max(0, actual() - 1)); }
    });

    /* Arrastre con ratón (en táctil ya desliza solo) */
    var x0 = 0, s0 = 0, abajo = false, movido = false;
    pista.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse") return;
      abajo = true; movido = false; x0 = e.clientX; s0 = pista.scrollLeft;
    });
    window.addEventListener("pointermove", function (e) {
      if (!abajo) return;
      var dx = e.clientX - x0;
      if (Math.abs(dx) > 4) { movido = true; pista.classList.add("arrastrando"); }
      pista.scrollLeft = s0 - dx;
    });
    window.addEventListener("pointerup", function () {
      if (!abajo) return;
      abajo = false;
      if (movido) { pista.classList.remove("arrastrando"); ir(actual()); }
    });
    pintar();
  });
})();

/* Asistente de la web (respuestas preparadas, sin servidor) */
(function () {
  var raiz = document.querySelector(".bot"), datosEl = document.getElementById("bot-datos");
  if (!raiz || !datosEl) return;
  var D; try { D = JSON.parse(datosEl.textContent); } catch (e) { return; }
  var panel = raiz.querySelector(".bot-panel"), boton = raiz.querySelector(".bot-boton");
  var msgs = raiz.querySelector(".bot-msgs"), form = raiz.querySelector(".bot-form"), input = raiz.querySelector("#bot-texto");
  var temas = {}, historial = [], empezado = false;
  D.temas.forEach(function (t) { temas[t.id] = t; });
  function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9ñ ]/g, " ").replace(/\s+/g, " ").trim(); }
  function bajar() { msgs.scrollTop = msgs.scrollHeight; }
  function burbuja(txt, quien) {
    var p = document.createElement("div"); p.className = "bot-m bot-m--" + quien; p.textContent = txt;
    msgs.appendChild(p); bajar(); return p;
  }
  function correoUrl() {
    var cuerpo = "Hola Juanra,\n\n" + (historial.length ? "Te escribo desde tu web. Te preguntaba:\n- " + historial.join("\n- ") + "\n\n" : "") + "Mi nombre y empresa: \n";
    return "mailto:" + D.correo + "?subject=" + encodeURIComponent(D.correo_asunto || "Consulta") + "&body=" + encodeURIComponent(cuerpo);
  }
  function opciones(ids, conCorreo) {
    var c = document.createElement("div"); c.className = "bot-ops";
    (ids || []).forEach(function (id) {
      var t = temas[id]; if (!t || !t.boton) return;
      var b = document.createElement("button"); b.type = "button"; b.className = "bot-op"; b.textContent = t.boton;
      b.addEventListener("click", function () { burbuja(t.boton, "yo"); responder(t); });
      c.appendChild(b);
    });
    if (conCorreo && D.agenda) {
      var ag = document.createElement("a"); ag.className = "bot-op bot-op--correo"; ag.href = D.agenda; ag.target = "_blank"; ag.rel = "noopener"; ag.textContent = "Reservar una reunión";
      c.appendChild(ag);
    }
    if (conCorreo) {
      var a = document.createElement("a"); a.className = "bot-op bot-op--correo"; a.href = correoUrl(); a.textContent = "Escribir a Juanra";
      c.appendChild(a);
    }
    if (c.children.length) { msgs.appendChild(c); bajar(); }
  }
  function responder(t) {
    setTimeout(function () {
      var p = burbuja(t.texto, "bot");
      if (t.enlace) {
        var a = document.createElement("a"); a.className = "bot-link"; a.href = t.enlace.url; a.textContent = t.enlace.texto + " →";
        if (/^https?:/.test(t.enlace.url)) { a.target = "_blank"; a.rel = "noopener"; }
        p.appendChild(document.createElement("br")); p.appendChild(a);
      }
      opciones(t.siguientes, t.accion === "correo" || !(t.siguientes || []).length || t.siguientes.indexOf("contacto") < 0);
    }, 350);
  }
  function buscar(q) {
    var n = " " + norm(q) + " ", mejor = null, max = 0;
    D.temas.forEach(function (t) {
      var p = 0;
      (t.claves || []).forEach(function (k) {
        var kk = norm(k); if (!kk) return;
        if (n.indexOf(" " + kk + " ") >= 0) p += 3 + kk.split(" ").length;
        else if (kk.length > 4 && n.indexOf(kk.slice(0, -1)) >= 0) p += 1;
      });
      if (p > max) { max = p; mejor = t; }
    });
    return max >= 2 ? mejor : null;
  }
  function empezar() {
    if (empezado) return; empezado = true;
    burbuja(D.saludo, "bot"); opciones(D.inicio, false);
  }
  function abrir(si) {
    panel.hidden = !si; boton.setAttribute("aria-expanded", si ? "true" : "false"); raiz.classList.toggle("abierto", si);
    if (si) { empezar(); setTimeout(function () { input.focus(); }, 50); }
  }
  boton.addEventListener("click", function () { abrir(panel.hidden); });
  raiz.querySelector(".bot-cerrar").addEventListener("click", function () { abrir(false); boton.focus(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) abrir(false); });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim(); if (!q) return;
    input.value = ""; burbuja(q, "yo"); historial.push(q);
    var t = buscar(q);
    if (t) responder(t);
    else setTimeout(function () { burbuja(D.no_entiendo, "bot"); opciones(["servicios", "formacion-equipos"], true); }, 350);
  });
})();

/* «Hablemos» de Ciclista: el sonido del vídeo suena cuando el vídeo está en pantalla y se apaga al salir.
   Los navegadores solo dejan poner sonido después de que la persona haya tocado o pulsado algo en la página,
   así que el sonido se activa con la primera interacción (o con el botón) y queda el botón para silenciarlo. */
(function () {
  var sec = document.querySelector(".cierre--video");
  if (!sec) return;
  var v = sec.querySelector(".cierre-video");
  var b = sec.querySelector(".cierre-sonido");
  if (!v || !b) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) { b.hidden = true; return; }
  var guardado = null;
  try { guardado = sessionStorage.getItem("jd-sonido"); } catch (e) {}
  var permitido = false, silenciado = guardado === "no", visible = false, temporizador = null;

  function fundido(destino, alAcabar) {
    clearInterval(temporizador);
    var pasos = 12, i = 0, inicio = v.muted ? 0 : v.volume;
    temporizador = setInterval(function () {
      i++;
      try { v.volume = Math.max(0, Math.min(1, inicio + (destino - inicio) * (i / pasos))); } catch (e) {}
      if (i >= pasos) { clearInterval(temporizador); if (alAcabar) alAcabar(); }
    }, 35);
  }
  function boton() {
    var on = permitido && !silenciado;
    b.setAttribute("aria-pressed", on ? "true" : "false");
    b.classList.toggle("activo", on);
    b.querySelector(".cierre-sonido-texto").textContent = on ? "Silenciar" : "Activar sonido";
  }
  function aplicar() {
    if (permitido && !silenciado && visible) {
      try { v.volume = 0; } catch (e) {}
      v.muted = false;
      var p = v.play();
      if (p && p.catch) p.catch(function () { v.muted = true; v.play(); permitido = false; boton(); });
      if (v.paused) { v.muted = true; v.play(); }
      fundido(1);
    } else if (!v.muted) {
      fundido(0, function () { v.muted = true; });
    }
    boton();
  }
  function primeraInteraccion(e) {
    if (b.contains(e.target)) return;
    if (!permitido) { permitido = true; aplicar(); }
    ["pointerdown", "keydown", "touchend"].forEach(function (t) { document.removeEventListener(t, primeraInteraccion, true); });
  }
  ["pointerdown", "keydown", "touchend"].forEach(function (t) { document.addEventListener(t, primeraInteraccion, true); });

  b.addEventListener("click", function () {
    if (permitido && !silenciado) { silenciado = true; } else { permitido = true; silenciado = false; }
    try { sessionStorage.setItem("jd-sonido", silenciado ? "no" : "si"); } catch (e) {}
    aplicar();
  });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entradas) {
      visible = entradas[0].isIntersecting;
      aplicar();
    }, { threshold: 0.5 }).observe(sec);
  }
  document.addEventListener("visibilitychange", function () { if (document.hidden && !v.muted) { v.muted = true; } else if (!document.hidden) { aplicar(); } });
  boton();
})();
