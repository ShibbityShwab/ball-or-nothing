// BALL OR NOTHING - symbol artwork.
//
// Lighting contract, shared by every symbol so the board reads as one coherent set:
//   key light   upper-left, warm
//   rim light   lower-right, cool
//   ambient     deep navy, from below
//   material    glossy, one bold specular per symbol
//
// Ids are suffixed per call so the same symbol can appear many times on one board without
// gradient collisions.

let uid = 0;

const hex = (id) => `${id}${uid}`;

function svg(inner, defs) {
  uid += 1;
  return `<svg viewBox="0 0 100 100" class="sym-svg" aria-hidden="true"><defs>${defs}</defs>${inner}</svg>`;
}

function ball() {
  const body = hex("ballBody");
  const sheen = hex("ballSheen");
  return svg(
    `<circle cx="50" cy="53" r="38" fill="url(#${body})"/>
     <ellipse cx="50" cy="53" rx="38" ry="38" fill="url(#${sheen})" opacity="0.5"/>
     <ellipse cx="35" cy="31" rx="14" ry="8.5" fill="#fffdf2" opacity="0.85" transform="rotate(-28 35 31)"/>
     <ellipse cx="62" cy="74" rx="9" ry="4" fill="#2b1d06" opacity="0.5" transform="rotate(-20 62 74)"/>
     <path d="M88 57 A38 38 0 0 1 62 89" fill="none" stroke="#ffe9a8" stroke-width="2.4" stroke-linecap="round" opacity="0.75"/>`,
    `<radialGradient id="${body}" cx="34%" cy="28%" r="78%">
       <stop offset="0%" stop-color="#fff6d0"/>
       <stop offset="30%" stop-color="#f7c757"/>
       <stop offset="68%" stop-color="#c98f22"/>
       <stop offset="100%" stop-color="#5b3d0b"/>
     </radialGradient>
     <radialGradient id="${sheen}" cx="50%" cy="50%" r="50%">
       <stop offset="70%" stop-color="#000" stop-opacity="0"/>
       <stop offset="100%" stop-color="#1b1204" stop-opacity="0.85"/>
     </radialGradient>`
  );
}

function nut() {
  const face = hex("nutFace");
  const hole = hex("nutHole");
  return svg(
    `<path d="M50 12 L84 32 L84 70 L50 90 L16 70 L16 32 Z" fill="url(#${face})"/>
     <path d="M50 12 L84 32 L84 70 L50 90 Z" fill="#000" opacity="0.14"/>
     <circle cx="50" cy="51" r="16.5" fill="url(#${hole})"/>
     <circle cx="50" cy="51" r="16.5" fill="none" stroke="#3a2508" stroke-width="2.4"/>
     <path d="M35 35 L50 27 L65 35" fill="none" stroke="#ffd98a" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
     <path d="M84 70 L84 32" fill="none" stroke="#ffe9a8" stroke-width="2.2" opacity="0.55"/>`,
    `<linearGradient id="${face}" x1="18%" y1="10%" x2="82%" y2="92%">
       <stop offset="0%" stop-color="#f2c078"/>
       <stop offset="42%" stop-color="#c9803a"/>
       <stop offset="100%" stop-color="#6b4118"/>
     </linearGradient>
     <radialGradient id="${hole}" cx="42%" cy="34%" r="70%">
       <stop offset="0%" stop-color="#5a3a12"/>
       <stop offset="100%" stop-color="#1d1206"/>
     </radialGradient>`
  );
}

function sack() {
  const body = hex("sackBody");
  return svg(
    `<path d="M34 30 C22 44 16 58 20 72 C24 87 40 92 50 92 C60 92 76 87 80 72 C84 58 78 44 66 30 Z" fill="url(#${body})"/>
     <path d="M34 30 L66 30 L62 22 L38 22 Z" fill="#8a5a22"/>
     <path d="M37 24 L63 24" stroke="#5d3a12" stroke-width="3.4" stroke-linecap="round"/>
     <path d="M30 62 C34 74 44 80 52 80" fill="none" stroke="#3f2710" stroke-width="2.2" opacity="0.45" stroke-linecap="round"/>
     <text x="50" y="70" text-anchor="middle" font-family="Georgia, serif" font-size="30" font-weight="700" fill="#3d2409" opacity="0.82">$</text>
     <path d="M72 46 C78 58 78 70 72 82" fill="none" stroke="#ffd9a0" stroke-width="2.6" opacity="0.55" stroke-linecap="round"/>`,
    `<linearGradient id="${body}" x1="20%" y1="8%" x2="80%" y2="96%">
       <stop offset="0%" stop-color="#d9a35c"/>
       <stop offset="45%" stop-color="#a9713a"/>
       <stop offset="100%" stop-color="#5c3814"/>
     </linearGradient>`
  );
}

function coin() {
  const face = hex("coinFace");
  const rim = hex("coinRim");
  return svg(
    `<ellipse cx="50" cy="55" rx="37" ry="37" fill="url(#${rim})"/>
     <ellipse cx="50" cy="52" rx="32" ry="32" fill="url(#${face})"/>
     <ellipse cx="50" cy="52" rx="26" ry="26" fill="none" stroke="#8a6116" stroke-width="1.6" opacity="0.6"/>
     <ellipse cx="36" cy="36" rx="10" ry="6" fill="#fffdf0" opacity="0.6" transform="rotate(-30 36 36)"/>
     <path d="M50 30 L57 45 L73 47 L61 58 L64 74 L50 66 L36 74 L39 58 L27 47 L43 45 Z"
           fill="#9a6d1a" opacity="0.85"/>
     <path d="M50 34 L56 47 L69 48 L59 57 L62 70 L50 63 L38 70 L41 57 L31 48 L44 47 Z"
           fill="#ffe9a8" opacity="0.85"/>`,
    `<radialGradient id="${face}" cx="36%" cy="30%" r="76%">
       <stop offset="0%" stop-color="#fff7d6"/>
       <stop offset="52%" stop-color="#e8bc4c"/>
       <stop offset="100%" stop-color="#96690f"/>
     </radialGradient>
     <radialGradient id="${rim}" cx="40%" cy="34%" r="74%">
       <stop offset="0%" stop-color="#a8791d"/>
       <stop offset="100%" stop-color="#4a3208"/>
     </radialGradient>`
  );
}

function wild() {
  const core = hex("wildCore");
  const rays = hex("wildRays");
  return svg(
    `<path d="M50 6 L60 34 L88 26 L70 48 L94 62 L64 64 L72 92 L50 72 L28 92 L36 64 L6 62 L30 48 L12 26 L40 34 Z"
           fill="url(#${rays})"/>
     <circle cx="50" cy="52" r="21" fill="url(#${core})"/>
     <circle cx="50" cy="52" r="21" fill="none" stroke="#eafff2" stroke-width="1.8" opacity="0.7"/>
     <path d="M42 41 L62 52 L42 63 Z" fill="#0d3b22" opacity="0.9"/>
     <circle cx="42" cy="42" r="6" fill="#f2fff7" opacity="0.6"/>`,
    `<linearGradient id="${rays}" x1="20%" y1="4%" x2="80%" y2="96%">
       <stop offset="0%" stop-color="#c9ffe0"/>
       <stop offset="55%" stop-color="#4fd486"/>
       <stop offset="100%" stop-color="#1c7a48"/>
     </linearGradient>
     <radialGradient id="${core}" cx="36%" cy="30%" r="76%">
       <stop offset="0%" stop-color="#ffffff"/>
       <stop offset="55%" stop-color="#7bd88f"/>
       <stop offset="100%" stop-color="#2f9c5c"/>
     </radialGradient>`
  );
}

function vault() {
  const door = hex("vaultDoor");
  const dial = hex("vaultDial");
  return svg(
    `<rect x="12" y="12" width="76" height="76" rx="9" fill="url(#${door})"/>
     <rect x="12" y="12" width="76" height="76" rx="9" fill="none" stroke="#2a2f38" stroke-width="3"/>
     <rect x="20" y="20" width="60" height="60" rx="5" fill="none" stroke="#151a20" stroke-width="2" opacity="0.7"/>
     <circle cx="50" cy="50" r="19" fill="url(#${dial})"/>
     <circle cx="50" cy="50" r="19" fill="none" stroke="#1b2028" stroke-width="2.4"/>
     <circle cx="50" cy="50" r="5.5" fill="#12161c"/>
     <g stroke="#1b2028" stroke-width="3.4" stroke-linecap="round">
       <path d="M50 31 L50 22"/><path d="M50 69 L50 78"/>
       <path d="M31 50 L22 50"/><path d="M69 50 L78 50"/>
     </g>
     <circle cx="24" cy="24" r="3.4" fill="#0f1319"/><circle cx="76" cy="24" r="3.4" fill="#0f1319"/>
     <circle cx="24" cy="76" r="3.4" fill="#0f1319"/><circle cx="76" cy="76" r="3.4" fill="#0f1319"/>
     <path d="M12 18 L12 12 L18 12" fill="none" stroke="#ff9d9d" stroke-width="2.6"/>
     <path d="M82 88 L88 88 L88 82" fill="none" stroke="#ff6b6b" stroke-width="2.6"/>`,
    `<linearGradient id="${door}" x1="16%" y1="8%" x2="84%" y2="94%">
       <stop offset="0%" stop-color="#8d97a5"/>
       <stop offset="48%" stop-color="#5b6472"/>
       <stop offset="100%" stop-color="#2c333d"/>
     </linearGradient>
     <radialGradient id="${dial}" cx="36%" cy="30%" r="76%">
       <stop offset="0%" stop-color="#e8ecf2"/>
       <stop offset="60%" stop-color="#9aa4b2"/>
       <stop offset="100%" stop-color="#4b535f"/>
     </radialGradient>`
  );
}

function loss() {
  const body = hex("lossBody");
  uid += 1;
  return `<svg viewBox="0 0 100 100" class="sym-svg" aria-hidden="true"><defs>
    <radialGradient id="${body}" cx="38%" cy="32%" r="76%">
      <stop offset="0%" stop-color="#3c4150"/>
      <stop offset="60%" stop-color="#1e222c"/>
      <stop offset="100%" stop-color="#0c0e13"/>
    </radialGradient>
  </defs>
  <circle cx="50" cy="52" r="35" fill="url(#${body})"/>
  <path d="M28 38 L46 50 L32 62 L52 70" fill="none" stroke="#555c6c" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M62 26 L54 48 L68 52 L58 78" fill="none" stroke="#6b7386" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.8"/>
  <circle cx="50" cy="52" r="35" fill="none" stroke="#2b303c" stroke-width="2"/>
  </svg>`;
}

const BUILDERS = { BALL: ball, NUT: nut, SACK: sack, COIN: coin, WILD: wild, VAULT: vault, LOSS: loss };

export function symbolArt(name) {
  const build = BUILDERS[name];
  return build ? build() : "";
}

// Generated overrides. `tools/generate_assets.mjs` writes frontend/assets/manifest.json;
// when it exists the game prefers those images over the drawn art, so shipping a
// generated set is a regenerate-and-reload rather than a code change. Absent manifest
// means the SVG set above is used and nothing else changes.
let generated = null;

export async function loadGeneratedAssets() {
  try {
    const res = await fetch("./assets/manifest.json", { cache: "no-store" });
    if (!res.ok) return null;
    const manifest = await res.json();
    generated = manifest?.symbols ?? null;
    return generated;
  } catch {
    return null;
  }
}

export function generatedArt(name) {
  const files = generated?.[name];
  return Array.isArray(files) && files.length ? `./assets/generated/${files[0]}` : null;
}

export function brandMark(size = 56) {
  return `<svg viewBox="0 0 100 100" width="${size}" height="${size}" class="brand-svg" aria-hidden="true">
    <defs>
      <radialGradient id="bmBody" cx="34%" cy="28%" r="78%">
        <stop offset="0%" stop-color="#fff6d0"/>
        <stop offset="30%" stop-color="#f7c757"/>
        <stop offset="68%" stop-color="#c98f22"/>
        <stop offset="100%" stop-color="#5b3d0b"/>
      </radialGradient>
      <radialGradient id="bmSheen" cx="50%" cy="50%" r="50%">
        <stop offset="68%" stop-color="#000" stop-opacity="0"/>
        <stop offset="100%" stop-color="#1b1204" stop-opacity="0.8"/>
      </radialGradient>
    </defs>
    <circle cx="50" cy="53" r="38" fill="url(#bmBody)"/>
    <circle cx="50" cy="53" r="38" fill="url(#bmSheen)"/>
    <ellipse cx="35" cy="31" rx="14" ry="8.5" fill="#fffdf2" opacity="0.9" transform="rotate(-28 35 31)"/>
    <path d="M88 57 A38 38 0 0 1 62 89" fill="none" stroke="#ffe9a8" stroke-width="2.6" stroke-linecap="round" opacity="0.8"/>
  </svg>`;
}
