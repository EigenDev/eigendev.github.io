// =============================================================================
// terminal.js
//
// progressive-enhancement behavior for the terminal theme:
// - live utc-ish clock in the status bar
// - current year in the footer
// - typewriter reveal of the boot "whoami" command + output lines
//
// all content is present in the dom without js; this only animates it.
// =============================================================================

(function () {
  "use strict";

  document.documentElement.classList.add("js");

  // -- theme cycling ---------------------------------------------------------
  // cycles mint -> gruvbox-dark -> gruvbox-light; persisted in localStorage.
  // the head boot script applies the saved theme pre-paint; this just cycles.
  var THEMES = ["mint", "gruvbox-dark", "gruvbox-light"];
  var themeSeg = document.getElementById("themeSeg");
  var themeToggle = document.getElementById("themeToggle");

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") || "mint";
  }

  function applyTheme(name) {
    if (name === "mint") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", name);
    }
    if (themeSeg) themeSeg.textContent = name;
    try { localStorage.setItem("theme", name); } catch (e) {}
  }

  if (themeSeg) themeSeg.textContent = currentTheme();
  if (themeToggle) {
    themeToggle.addEventListener("click", function (ev) {
      ev.preventDefault();
      var next = THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length];
      applyTheme(next);
    });
  }

  // -- live clock + year -----------------------------------------------------
  var clock = document.getElementById("clock");
  var year = document.getElementById("year");

  function pad(nn) { return nn < 10 ? "0" + nn : "" + nn; }

  function tick() {
    if (!clock) return;
    var d = new Date();
    clock.textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  }

  if (year) year.textContent = new Date().getFullYear();
  tick();
  setInterval(tick, 1000);

  // -- boot typewriter -------------------------------------------------------
  // types the whoami command, then fades in the reveal lines in sequence.
  var target = document.querySelector(".type-target");
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".typed .reveal"));

  if (!target) return;

  var text = target.getAttribute("data-text") || target.textContent;

  // reduced-motion: skip the typewriter, show everything at once.
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    target.textContent = text;
    reveals.forEach(function (el) { el.classList.add("show"); });
    return;
  }

  target.textContent = "";

  var ii = 0;
  function typeChar() {
    if (ii <= text.length) {
      target.textContent = text.slice(0, ii);
      ii += 1;
      setTimeout(typeChar, 45);
    } else {
      revealNext(0);
    }
  }

  function revealNext(jj) {
    if (jj >= reveals.length) return;
    reveals[jj].classList.add("show");
    setTimeout(function () { revealNext(jj + 1); }, 260);
  }

  // small delay so the motd is read first
  setTimeout(typeChar, 500);
})();
