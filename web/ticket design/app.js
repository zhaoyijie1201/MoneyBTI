const personas = Array.isArray(window.MONEYBTI_PERSONAS) ? window.MONEYBTI_PERSONAS : [];
const personaRules = Array.isArray(window.MONEYBTI_PERSONA_RULES) ? window.MONEYBTI_PERSONA_RULES : [];
const byCode = Object.fromEntries(personas.map((persona) => [persona.code, persona]));
const picker = document.querySelector("#personaSelect");
const ticket = document.querySelector("#ticket");
const status = document.querySelector("#dataStatus");

function setField(name, value) {
  document.querySelectorAll(`[data-field="${name}"]`).forEach((element) => { element.textContent = value ?? ""; });
}

function renderDemoPersona(persona, payload = {}) {
  if (!persona) return;
  const data = {...persona, ...payload, indices: Array.isArray(payload.indices) ? payload.indices : persona.indices};
  const index = personas.findIndex((item) => item.code === persona.code) + 1;
  const number = String(4870 + index).padStart(6, "0");
  const fields = {
    file: `FILE / ${String(index).padStart(2, "0")}—${data.code}`,
    category: `SPENDING PERSONA · ${data.category}`,
    titleTop: data.title[0], titleBottom: data.title[1], code: data.code,
    number: `NO. ${number}`, observation: `OBSERVATION NO. ${number}`,
    caption: data.caption, quoteTop: data.quote[0], quoteBottom: data.quote[1],
    type: data.type, match: data.match, rarity: data.rarity,
    total: data.total, transactions: data.transactions, merchant: data.merchant,
    signal: data.signal, findingTitle: data.findingTitle,
    description: data.description, tagline: data.tagline
  };
  Object.entries(fields).forEach(([name, value]) => setField(name, value));
  const image = document.querySelector("#personaImage");
  image.src = data.image;
  image.alt = data.alt;
  const longestLine = Math.max(...data.title.map((line) => line.length));
  ticket.dataset.titleSize = longestLine > 13 ? "long" : longestLine > 9 ? "medium" : "short";
  const indices = document.querySelector("#indices");
  indices.replaceChildren();
  data.indices.forEach(([label, score], position) => {
    const row = document.createElement("div");
    row.className = "index";
    row.style.setProperty("--score", `${score}%`);
    const text = document.createElement("p");
    const name = document.createElement("span");
    name.textContent = label;
    const value = document.createElement("b");
    value.textContent = score;
    text.append(name, value);
    const bar = document.createElement("i");
    bar.setAttribute("aria-hidden", "true");
    row.append(text, bar);
    indices.append(row);
    if (typeof row.animate === "function") {
      row.animate([{opacity:0,transform:"translateY(8px)"},{opacity:1,transform:"translateY(0)"}],{duration:340,delay:position*55,easing:"cubic-bezier(.2,.8,.2,1)",fill:"both"});
    }
  });
  picker.value = data.code;
  document.title = `MoneyBTI · ${data.name} · DEMO DATA`;
  if (/^https?:$/.test(window.location.protocol)) {
    const url = new URL(window.location.href);
    url.searchParams.set("persona", data.code);
    history.replaceState(null, "", url);
  }
}

async function requestPersonalityAnalysis(input) {
  // Future backend integration point: POST /api/personality-analysis
  // Request: {transactions: [], period: {start: "", end: ""}}
  // Response: {code, match, total, transactions, merchant, signal, indices}
  if (!/^https?:$/.test(window.location.protocol)) return null;
  try {
    const response = await fetch("/api/personality-analysis", {
      method: "POST",
      headers: {"Accept":"application/json", "Content-Type":"application/json"},
      body: JSON.stringify(input)
    });
    if (!response.ok) return null;
    const payload = await response.json();
    if (!payload || typeof payload !== "object" || !byCode[payload.code]) return null;
    return payload;
  } catch {
    return null;
  }
}

function selectLocalDemo(code) {
  const persona = byCode[code] || personas[0];
  renderDemoPersona(persona);
  status.textContent = "DEMO DATA";
}

async function initialize() {
  const requested = new URLSearchParams(window.location.search).get("persona") || personas[0]?.code;
  const fallback = byCode[requested] || personas[0];
  renderDemoPersona(fallback);
  status.textContent = "DEMO DATA";
  if (!/^https?:$/.test(window.location.protocol)) return;
  const payload = await requestPersonalityAnalysis({transactions: [], period: {start: "", end: ""}});
  if (!payload) return;
  renderDemoPersona(byCode[payload.code], payload);
  status.textContent = "BACKEND DATA";
}

personas.forEach((persona) => {
  const option = document.createElement("option");
  option.value = persona.code;
  option.textContent = `${persona.code} — ${persona.name} / ${persona.englishName}`;
  picker.append(option);
});

picker.addEventListener("change", () => selectLocalDemo(picker.value));
void initialize();

// Expose immutable knowledge sources for future local analysis without coupling them to rendering.
window.MONEYBTI_DEMO = Object.freeze({personas, personaRules, requestPersonalityAnalysis, renderDemoPersona});
