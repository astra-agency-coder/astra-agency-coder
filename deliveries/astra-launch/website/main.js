/* AI ASTRA AGENCY — site behaviour (progressive enhancement only).
   No tracking, no external requests. The page is fully readable without JS. */
(function () {
  "use strict";

  document.documentElement.classList.remove("no-js");

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Reveal-on-scroll. Classes are added by JS, so content stays visible
  // when JS is unavailable or disabled.
  var targets = document.querySelectorAll(".card, .step, .callout, .hero-facts li");
  if (!targets.length) return;

  if (reduceMotion || !("IntersectionObserver" in window)) {
    // Nothing to do: elements are already visible by default.
    return;
  }

  Array.prototype.forEach.call(targets, function (el) {
    el.classList.add("reveal");
  });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.1 });

  Array.prototype.forEach.call(targets, function (el) {
    observer.observe(el);
  });
})();
