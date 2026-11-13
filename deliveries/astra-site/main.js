/* AI ASTRA AGENCY — site interactions */
(() => {
  "use strict";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ── hero reveal on load ───────────────────────────── */
  addEventListener("load", () => {
    document.body.classList.add("is-ready");
    $$(".reveal").forEach(el => {
      el.style.setProperty("--d", el.dataset.delay || 0);
    });
  }, { once: true });

  /* ── scroll reveal ─────────────────────────────────── */
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.style.setProperty("--d", e.target.dataset.delay || 0);
      e.target.classList.add("is-in");
      io.unobserve(e.target);
    });
  }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });
  $$(".reveal").forEach(el => io.observe(el));

  /* ── nav: stuck state + mobile toggle ──────────────── */
  const nav = $("#nav"), toggle = $("#navToggle"), links = $(".nav__links");
  const onScroll = () => nav.classList.toggle("is-stuck", scrollY > 24);
  onScroll();
  addEventListener("scroll", onScroll, { passive: true });
  toggle?.addEventListener("click", () => {
    const open = links.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  $$(".nav__links a").forEach(a => a.addEventListener("click", () => {
    links.classList.remove("is-open");
    toggle?.setAttribute("aria-expanded", "false");
  }));

  /* ── progress bar ──────────────────────────────────── */
  const bar = $("#progressBar");
  const progress = () => {
    const h = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = (h > 0 ? (scrollY / h) * 100 : 0) + "%";
  };
  progress();
  addEventListener("scroll", progress, { passive: true });
  addEventListener("resize", progress);

  /* ── count-up stats ────────────────────────────────── */
  const countIO = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el = e.target, to = +el.dataset.count, sfx = el.dataset.suffix || "";
      const t0 = performance.now(), dur = 1400;
      const tick = (t) => {
        const p = Math.min(1, (t - t0) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(to * eased) + sfx;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      countIO.unobserve(el);
    });
  }, { threshold: 0.5 });
  $$(".stat__n").forEach(el => countIO.observe(el));

  /* ── custom cursor ─────────────────────────────────── */
  if (!reduce && matchMedia("(hover:hover)").matches) {
    const c = $(".cursor"), dot = $(".cursor__dot"), ring = $(".cursor__ring");
    let x = innerWidth / 2, y = innerHeight / 2, rx = x, ry = y;
    addEventListener("mousemove", (e) => { x = e.clientX; y = e.clientY; });
    const loop = () => {
      rx += (x - rx) * 0.18; ry += (y - ry) * 0.18;
      dot.style.transform = `translate(${x}px,${y}px) translate(-50%,-50%)`;
      ring.style.transform = `translate(${rx}px,${ry}px) translate(-50%,-50%)`;
      requestAnimationFrame(loop);
    };
    loop();
    $$("a,button,input,textarea,.card,.work__item").forEach(el => {
      el.addEventListener("mouseenter", () => c.classList.add("is-hot"));
      el.addEventListener("mouseleave", () => c.classList.remove("is-hot"));
    });
  }

  /* ── magnetic buttons ──────────────────────────────── */
  if (!reduce) {
    $$("[data-magnetic]").forEach(el => {
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const mx = e.clientX - r.left - r.width / 2;
        const my = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${mx * 0.18}px,${my * 0.28}px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* ── constellation canvas ──────────────────────────── */
  const cv = $("#field");
  if (cv && !reduce) {
    const ctx = cv.getContext("2d", { alpha: true });
    let w, h, dpr, pts = [];
    const DENSITY = 0.00009, LINK = 128;
    const resize = () => {
      dpr = Math.min(devicePixelRatio || 1, 2);
      w = cv.width = Math.floor(innerWidth * dpr);
      h = cv.height = Math.floor(innerHeight * dpr);
      cv.style.width = innerWidth + "px";
      cv.style.height = innerHeight + "px";
      const n = Math.max(28, Math.min(110, Math.floor(innerWidth * innerHeight * DENSITY)));
      pts = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.22 * dpr,
        vy: (Math.random() - 0.5) * 0.22 * dpr,
        r: (Math.random() * 1.5 + 0.5) * dpr
      }));
    };
    const step = () => {
      ctx.clearRect(0, 0, w, h);
      for (const p of pts) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
      }
      const L = LINK * dpr;
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const a = pts[i], b = pts[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 > L * L) continue;
          const o = (1 - Math.sqrt(d2) / L) * 0.34;
          ctx.strokeStyle = `rgba(155,184,245,${o})`;
          ctx.lineWidth = dpr * 0.6;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      for (const p of pts) {
        ctx.fillStyle = "rgba(201,176,240,.75)";
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      }
      requestAnimationFrame(step);
    };
    addEventListener("resize", resize);
    resize(); step();
  }

  /* ── contact form → real email ─────────────────────── */
  const form = $("#contactForm"), status = $("#formStatus"), btn = $("#submitBtn");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.className = "form__status";
    const data = Object.fromEntries(new FormData(form));
    if (!data.name?.trim() || !data.email?.trim() || !data.message?.trim()) {
      status.textContent = "Please fill in your name, email and brief.";
      status.classList.add("err"); return;
    }
    btn.disabled = true; btn.textContent = "Sending…";
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const out = await res.json().catch(() => ({}));
      if (res.ok && out.ok) {
        form.reset();
        status.textContent = "Thank you — your brief is on its way. We reply within one working day.";
        status.classList.add("ok");
      } else {
        status.textContent = out.error || "Something went wrong. Please try again.";
        status.classList.add("err");
      }
    } catch {
      status.textContent = "Network error — please try again, or email addh22010@gmail.com.";
      status.classList.add("err");
    } finally {
      btn.disabled = false; btn.textContent = "Send the brief";
    }
  });

  $("#year").textContent = new Date().getFullYear();
})();
