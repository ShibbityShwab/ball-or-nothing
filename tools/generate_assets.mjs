#!/usr/bin/env node
/**
 * Generate the BALL OR NOTHING symbol set with the Venice image API.
 *
 *   VENICE_API_KEY=... node tools/generate_assets.mjs
 *   VENICE_API_KEY=... node tools/generate_assets.mjs --model flux-2-pro --variants 2
 *
 * Venice's API is OpenAI-compatible for chat but NOT for images: it uses
 * POST /api/v1/image/generate with its own request shape, and returns base64 in
 * `images[]` unless `return_binary` is set. See:
 *   https://docs.venice.ai/api-reference/endpoint/image/generate
 *
 * Model sizing differs by family. Pixel models (venice-sd35) take width/height up to
 * 1280. Aspect-ratio models (qwen-image-*) REJECT width/height with a 400 and want
 * `aspect_ratio`. Resolution-tier models (gpt-image-2, nano-banana-*) take aspect_ratio
 * plus resolution. This script sends width/height, so it defaults to a pixel model.
 *
 * TRANSPARENCY: Venice has no background-transparency parameter. Symbols are generated
 * on a flat matte ground and the frontend feathers the edges with a radial mask (see
 * .symbol-art in styles.css), so the square boundary never shows on the reel.
 *
 * The prompts share one lighting contract with the hand-authored SVG set in
 * frontend/symbols.js, so a generated set and a drawn set look like the same game.
 */

import { mkdir, writeFile, rm } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT_DIR = path.join(ROOT, "frontend", "assets", "generated");
const MANIFEST = path.join(ROOT, "frontend", "assets", "manifest.json");

const ENDPOINT = "https://api.venice.ai/api/v1/image/generate";
const API_KEY = process.env.VENICE_API_KEY ?? process.env.VENICE_KEY ?? "";

// Models return ~1.3 MB at 1024px. Eight of those is 10.6 MB of sprites, which is
// indefensible for a web game when the largest a symbol is ever drawn is ~120 device
// pixels. Downscaling to 256 takes the set to ~800 KB with no visible difference.
const SPRITE_SIZE = 256;

// Matte ground the art is rendered against. It matches the reel background so any edge
// the mask leaves behind is invisible.
const GROUND = "#0a0c13";

// One style clause for every symbol, so the set reads as a family.
const STYLE = [
  "premium mobile slot-machine symbol",
  "glossy rendered 3D icon, chunky readable silhouette that still reads at 48px tall",
  "dramatic single-source key light from the upper left, cool rim light on the lower right",
  "deep navy ambient shadow underneath",
  "one bold specular highlight",
  "polished arcade casino art quality",
  "centered with a generous even margin",
  `flat matte ${GROUND} background, no scenery, no floor`,
  "no text, no letters, no numbers, no watermark, no logo, no border, no frame",
].join(", ");

const SYMBOLS = [
  {
    key: "BALL",
    subject:
      "a single gleaming golden sphere, warm metallic gold body with darker amber shading, " +
      "brushed-metal micro texture, bright specular highlight",
  },
  {
    key: "NUT",
    subject:
      "a hexagonal bronze hardware nut seen face-on, warm bronze metal, threaded bore through " +
      "the centre, machined bevels catching the light",
  },
  {
    key: "SACK",
    subject:
      "a small tied leather money bag, tan leather with visible stitching, a dollar sign " +
      "embossed into the front, gathered and knotted at the neck",
  },
  {
    key: "COIN",
    subject:
      "a thick gold casino coin standing slightly angled, ridged milled edge, a raised star " +
      "embossed on the face, heavy metallic weight",
  },
  {
    key: "WILD",
    subject:
      "a glowing emerald-green starburst of eight sharp rays with a lit core, luminous toxic " +
      "green energy, brighter than everything around it",
  },
  {
    key: "VAULT",
    subject:
      "a heavy steel bank vault door seen face-on, brushed gunmetal with a central spoked " +
      "combination dial and four corner bolts, a thin red hazard accent",
  },
  {
    key: "LOSS",
    subject:
      "a dark cracked stone sphere, almost black slate with a jagged fracture splitting it, " +
      "dull and recessed, deliberately the least appealing object in the set",
  },
];

const BRAND = {
  key: "BRAND",
  subject:
    "a single heroic golden sphere, the mascot icon of a gambling game, richer and more " +
    "polished than a plain ball, strong rim light, unmistakably the hero object",
};

function parseArgs(argv) {
  const opts = { model: "gpt-image-2-5-sunburst", variants: 1, size: 1024, only: null, dryRun: false, resize: SPRITE_SIZE };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--model") opts.model = argv[++i];
    else if (a === "--variants") opts.variants = Number(argv[++i]);
    else if (a === "--size") opts.size = Number(argv[++i]);
    else if (a === "--only") opts.only = argv[++i].toUpperCase();
    else if (a === "--resize") opts.resize = Number(argv[++i]);
    else if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--help" || a === "-h") opts.help = true;
  }
  return opts;
}

function usage() {
  console.log(`Generate the symbol set with Venice.

  VENICE_API_KEY=<key> node tools/generate_assets.mjs [options]

  --model NAME     image model (default gpt-image-2-5-sunburst; --model
                   gpt-image-2-5-flare is faster, venice-sd35 is cheapest)
  --variants N     images per symbol, 1-4 (default 1)
  --size N         square edge in px, max 1280 (default 1024)
  --resize N       downscale finished sprites to N px, 0 to skip (default 256)
  --only SYMBOL    generate one symbol: ${[...SYMBOLS, BRAND].map((s) => s.key).join(", ")}
  --dry-run        print the prompts and exit without calling the API

Models that size by aspect ratio (qwen-image-*) reject --size with a 400. List what your
key can use:  curl -s https://api.venice.ai/api/v1/models?type=image -H "Authorization: Bearer $VENICE_API_KEY"`);
}

// Sizing differs by model family and mixing the fields is a hard 400:
//   pixel models (venice-sd35)            -> width / height, <=1280
//   aspect models (qwen-image-*)          -> aspect_ratio, and they REJECT width/height
//   resolution models (gpt-image-2-*,     -> aspect_ratio + resolution
//     nano-banana-*)
// Rather than hard-code a table that goes stale as Venice adds models, the request is
// built from the model name and retried with the other scheme if the API rejects it.
function sizingFor(model, size, scheme) {
  if (scheme === "pixel") return { width: size, height: size };
  if (scheme === "ratio") return { aspect_ratio: "1:1", resolution: size >= 2048 ? "2K" : "1K" };
  return null;
}

function preferredScheme(model) {
  if (/^qwen-image/.test(model)) return "ratio";
  if (/^(gpt-image|nano-banana)/.test(model)) return "ratio";
  return "pixel";
}

async function generate(job, opts, scheme) {
  const body = {
    model: opts.model,
    prompt: `${job.subject}, ${STYLE}`,
    negative_prompt:
      "text, letters, numbers, watermark, signature, logo, border, frame, collage, grid, " +
      "multiple objects, busy background, scenery, blurry, low detail, flat 2d",
    variants: opts.variants,
    format: "png",
    // Venice can blur adult material when this is on. These are arcade objects, and a
    // blurred sprite would be useless, so it is off.
    safe_mode: false,
    hide_watermark: true,
    ...sizingFor(opts.model, opts.size, scheme),
  };

  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`${res.status} ${res.statusText}${text ? ` :: ${text.slice(0, 300)}` : ""}`);
    err.status = res.status;
    throw err;
  }

  const data = await res.json();
  if (!Array.isArray(data.images) || data.images.length === 0) {
    throw new Error(`no images in response: ${JSON.stringify(data).slice(0, 200)}`);
  }
  return data.images;
}

// Try the model's likely sizing scheme, then the other one. A 400 here is almost always
// the sizing field mismatch described above, not a bad prompt.
async function generateWithFallback(job, opts) {
  const first = preferredScheme(opts.model);
  const second = first === "pixel" ? "ratio" : "pixel";
  try {
    return await generate(job, opts, first);
  } catch (err) {
    if (err.status === 400) return generate(job, opts, second);
    throw err;
  }
}

// Downscale every generated sprite in place, keeping the originals in assets/raw so a
// re-run is never needed just to get a different size back. Uses .NET's imaging via
// PowerShell, which is present on Windows; other platforms get a clear note rather than a
// silent skip.
//
// The resize writes to a temp path first: System.Drawing keeps the source file open, so
// saving straight back onto it fails with a generic GDI+ error.
const RESIZE_PS = `
Add-Type -AssemblyName System.Drawing
$src = 'frontend/assets/generated'
$raw = 'frontend/assets/raw'
New-Item -ItemType Directory -Force -Path $raw | Out-Null
function Resize-Png([string]$inPath, [string]$outPath, [int]$size) {
  $img = [System.Drawing.Image]::FromFile($inPath)
  try {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    try {
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      try {
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.PixelOffsetMode   = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $g.SmoothingMode     = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $g.DrawImage($img, 0, 0, $size, $size)
      } finally { $g.Dispose() }
      $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $bmp.Dispose() }
  } finally { $img.Dispose() }
}
Get-ChildItem "$src\\*.png" | ForEach-Object {
  $orig = $_.FullName
  $backup = Join-Path $raw $_.Name
  if (-not (Test-Path $backup)) { Copy-Item $orig $backup -Force }
  $tmp = Join-Path $env:TEMP ('rz_' + $_.Name)
  Resize-Png $orig $tmp $SIZE
  Move-Item $tmp $orig -Force
}
`;

async function resizeSprites(size) {
  if (process.platform !== "win32") {
    console.log(`\nSkipping --resize: this relies on .NET imaging via PowerShell (Windows).`);
    console.log(`Resize frontend/assets/generated/*.png to ${size}px with your own tool.`);
    return false;
  }
  const script = RESIZE_PS.replace("$SIZE", String(size));
  const file = path.join(ROOT, ".resize.tmp.ps1");
  await writeFile(file, script, "utf8");
  try {
    await execFileAsync(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", file],
      { cwd: ROOT, timeout: 120000 },
    );
    return true;
  } finally {
    await rm(file, { force: true });
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return usage();

  const jobs = opts.only ? [...SYMBOLS, BRAND].filter((s) => s.key === opts.only) : [...SYMBOLS, BRAND];
  if (jobs.length === 0) {
    console.error(`--only ${opts.only} matched nothing`);
    return 1;
  }

  if (opts.dryRun) {
    for (const job of jobs) {
      console.log(`\n=== ${job.key} ===`);
      console.log(`${job.subject}, ${STYLE}`);
    }
    return 0;
  }

  if (!API_KEY) {
    console.error(
      "VENICE_API_KEY is not set.\n" +
        "  Get one at https://venice.ai/settings/api\n" +
        "  PowerShell (persists for new shells):  setx VENICE_API_KEY \"<key>\"\n" +
        "  This shell only:                       $env:VENICE_API_KEY = \"<key>\"\n" +
        "\nRun with --dry-run to preview the prompts without a key.",
    );
    return 1;
  }

  await mkdir(OUT_DIR, { recursive: true });

  const manifest = { model: opts.model, size: opts.size, generated: new Date().toISOString(), symbols: {} };
  let failures = 0;

  for (const job of jobs) {
    process.stdout.write(`${job.key.padEnd(6)} generating (${opts.variants}x ${opts.size}px)... `);
    try {
      const images = await generateWithFallback(job, opts);
      const files = [];
      for (let i = 0; i < images.length; i++) {
        const name = images.length === 1 ? `${job.key}.png` : `${job.key}-${i + 1}.png`;
        await writeFile(path.join(OUT_DIR, name), Buffer.from(images[i], "base64"));
        files.push(name);
      }
      manifest.symbols[job.key] = files;
      console.log(`ok -> ${files.join(", ")}`);
    } catch (err) {
      failures += 1;
      console.log(`FAILED: ${err.message}`);
    }
  }

  // A partial manifest is still useful, but say so rather than implying a full set.
  let resized = false;
  if (Object.keys(manifest.symbols).length && opts.resize > 0) {
    resized = await resizeSprites(opts.resize);
    if (resized) manifest.spriteSize = opts.resize;
  }

  await writeFile(MANIFEST, JSON.stringify(manifest, null, 2) + "\n", "utf8");

  console.log(`\nwrote ${Object.keys(manifest.symbols).length}/${jobs.length} symbols to frontend/assets/`);
  if (resized) console.log(`downscaled to ${opts.resize}px (originals kept in frontend/assets/raw/)`);
  console.log(`manifest: frontend/assets/manifest.json`);
  if (failures) {
    console.log(`${failures} failed - rerun, or use --only <SYMBOL> to retry just those.`);
  }
  console.log("\nReload the game; symbols.js picks the generated set up automatically.");
  return failures ? 1 : 0;
}

main()
  .then((code) => process.exit(code ?? 0))
  .catch((err) => {
    console.error(`\n${err.message}`);
    process.exit(1);
  });
