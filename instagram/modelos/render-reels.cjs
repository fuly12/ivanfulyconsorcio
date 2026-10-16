const { chromium } = require("playwright");
(async () => {
  const [html, out, modo, ...videos] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  const errors = [];
  p.on("pageerror", (e) => errors.push(String(e)));
  const fora = [];
  for (const v of videos) {
    await p.goto("about:blank");
    await p.goto(`file://${html}#${v}`, { waitUntil: "networkidle" });
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(200);
    if (modo === "chave") {
      for (const s of [2.0, 5.6, 8.6, 10.6, 13.6, 17.6]) {
        await p.evaluate((ms) => window.irPara(ms), s * 1000);
        const f = await p.evaluate(() => [...document.querySelectorAll(".cena *")].filter((el) => {
          const st = getComputedStyle(el); if (st.opacity === "0") return false;
          const r = el.getBoundingClientRect(); return r.width && (r.right > 931 || r.left < 89);
        }).map((el) => el.className.baseVal ?? el.className).slice(0, 3));
        if (f.length) fora.push(`v${v}@${s}: ${f.join(",")}`);
        await p.screenshot({ path: `${out}/v${v}-${String(s).padStart(4, "0")}.jpg`, type: "jpeg", quality: 85 });
      }
    } else {
      const fps = 30, total = 18 * fps;
      for (let f = 0; f < total; f++) {
        await p.evaluate((ms) => window.irPara(ms), (f * 1000) / fps);
        await p.screenshot({ path: `${out}/v${v}/f${String(f).padStart(4, "0")}.jpg`, type: "jpeg", quality: 94 });
      }
    }
  }
  console.log(JSON.stringify({ errors, fora }));
  await b.close();
})();
