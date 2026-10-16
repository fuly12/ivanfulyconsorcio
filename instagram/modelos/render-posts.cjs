const { chromium } = require("playwright");
const NOMES = [
  "01_sab-17-out_12h_chave-da-casa", "02_sab-17-out_19h_qual-seu-sonho",
  "03_dom-18-out_12h_carro-da-vitrine", "04_dom-18-out_19h_parcela-sem-juros",
  "05_seg-19-out_12h_moto", "06_seg-19-out_19h_precisa-de-um-plano",
  "07_ter-20-out_12h_quintal-da-sua-casa", "08_ter-20-out_19h_aluguel",
  "09_qua-21-out_12h_primeira-viagem", "10_qua-21-out_19h_sem-atalho-magico",
  "11_qui-22-out_12h_dinheiro-trabalhando", "12_qui-22-out_19h_me-conta-seu-sonho",
];
(async () => {
  const [html, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  const errors = [];
  p.on("pageerror", (e) => errors.push(String(e)));
  await p.goto("file://" + html, { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready);
  const problemas = [];
  for (let i = 1; i <= NOMES.length; i++) {
    await p.evaluate((n) => window.render(n), i);
    await p.waitForTimeout(120);
    const r = await p.evaluate(() => {
      const m = document.getElementById("main");
      const fora = [...m.querySelectorAll("*")].filter((el) => { const b = el.getBoundingClientRect(); return b.right > 1000.5 || b.left < 79.5; }).length;
      return { sobra: m.clientHeight - m.scrollHeight, fora };
    });
    if (r.sobra < 0 || r.fora) problemas.push(`${i}: ${JSON.stringify(r)}`);
    await p.screenshot({ path: `${out}/${NOMES[i - 1]}.png` });
  }
  console.log(JSON.stringify({ errors, problemas }));
  await b.close();
})();
