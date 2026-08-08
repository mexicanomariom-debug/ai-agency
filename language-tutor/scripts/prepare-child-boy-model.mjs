/**
 * Build webapp/public/models/child-boy.glb from CGTrader files in assets/child-boy/pack/
 *
 * A committed fallback GLB ships in the repo, so this script never fails the
 * build: without source files (CI, Vercel) it keeps the committed model, and a
 * broken custom model logs a warning instead of aborting the deploy.
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const packDir = path.join(root, "assets", "child-boy", "pack");
const sourceDir = path.join(root, "assets", "child-boy", "source");
const inputDirs = [packDir, sourceDir];
const outDir = path.join(root, "webapp", "public", "models");
const outFile = path.join(outDir, "child-boy.glb");
const fallbackUrl =
  "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@main/avatars/vroid.glb";

const ASSET_EXT = /\.(png|jpg|jpeg|webp|ktx2|bin)$/i;

/** 1×1 transparent PNG for missing CGTrader texture refs (e.g. Image.png). */
const PLACEHOLDER_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64",
);

function run(cmd) {
  console.log(cmd);
  execSync(cmd, { stdio: "inherit", cwd: root });
}

function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((n) => !n.startsWith("."));
}

function walkFiles(dir, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const name of fs.readdirSync(dir)) {
    if (name.startsWith(".")) continue;
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) walkFiles(full, acc);
    else acc.push(full);
  }
  return acc;
}

/** Normalize CGTrader names: spaces / pluses / underscores. */
function normalizeKey(name) {
  return decodeURIComponent(name)
    .toLowerCase()
    .replace(/\+/g, " ")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function findAsset(dir) {
  if (!fs.existsSync(dir)) return null;
  const names = listFiles(dir);
  const gltf = names.find(
    (n) => n.toLowerCase().endsWith(".gltf") && !n.toLowerCase().includes("model.fixed"),
  );
  if (gltf) return { path: path.join(dir, gltf), kind: "gltf" };
  const glb = names.find((n) => n.toLowerCase().endsWith(".glb") && !n.includes("child-boy"));
  if (glb) return { path: path.join(dir, glb), kind: "glb" };
  return null;
}

function findInputAsset() {
  for (const dir of inputDirs) {
    const hit = findAsset(dir);
    if (hit) return { ...hit, dir };
  }
  return null;
}

function unzipZip(zipPath, destDir) {
  const zip = path.resolve(zipPath);
  const dest = path.resolve(destDir);
  if (process.platform === "win32") {
    const ps = `Expand-Archive -LiteralPath '${zip.replace(/'/g, "''")}' -DestinationPath '${dest.replace(/'/g, "''")}' -Force`;
    const cmd = `powershell -NoProfile -ExecutionPolicy Bypass -Command "${ps}"`;
    console.log(cmd);
    execSync(cmd, { stdio: "inherit", cwd: root });
  } else {
    run(`unzip -o -q "${zip}" -d "${dest}"`);
  }
}

function unzipAllZips(dir) {
  for (const name of listFiles(dir)) {
    if (name.toLowerCase().endsWith(".zip")) {
      unzipZip(path.join(dir, name), dir);
    }
  }
}

function ensureFileBesideGltf(srcPath, destName, gltfDir) {
  const dest = path.join(gltfDir, destName);
  if (fs.existsSync(dest)) return dest;
  if (srcPath && fs.existsSync(srcPath)) {
    fs.copyFileSync(srcPath, dest);
    console.log(`Copied: ${destName}`);
  }
  return dest;
}

function findMatchingFile(wantedUri, assets, preferExt) {
  const raw = decodeURIComponent(wantedUri.split(/[/\\]/).pop() || wantedUri);
  const wantKey = normalizeKey(raw);
  const wantStem = normalizeKey(raw.replace(/\.[^.]+$/, ""));

  for (const f of assets) {
    if (normalizeKey(path.basename(f)) === wantKey) return f;
  }
  for (const f of assets) {
    const base = path.basename(f);
    if (preferExt && !base.toLowerCase().endsWith(preferExt)) continue;
    if (normalizeKey(base.replace(/\.[^.]+$/, "")) === wantStem) return f;
  }
  for (const f of assets) {
    const base = path.basename(f);
    if (preferExt && !base.toLowerCase().endsWith(preferExt)) continue;
    const stem = normalizeKey(base.replace(/\.[^.]+$/, ""));
    if (stem.includes(wantStem) || wantStem.includes(stem)) return f;
  }
  return null;
}

/** CGTrader: textures/bin may be nested; names use + vs spaces. */
function prepareGltfAssets(gltfPath, searchRoot) {
  const gltfDir = path.dirname(gltfPath);
  const assets = walkFiles(searchRoot).filter((f) => ASSET_EXT.test(f));

  for (const file of assets) {
    const base = path.basename(file);
    const dest = path.join(gltfDir, base);
    if (file !== dest && !fs.existsSync(dest)) {
      fs.copyFileSync(file, dest);
      console.log(`Copied: ${base}`);
    }
  }

  const localAssets = walkFiles(gltfDir).filter((f) => ASSET_EXT.test(f));
  const doc = JSON.parse(fs.readFileSync(gltfPath, "utf8"));

  const fixUriList = (list, preferExt, placeholder) => {
    if (!list) return;
    for (const item of list) {
      if (!item.uri || item.uri.startsWith("data:")) continue;
      const raw = decodeURIComponent(item.uri.split(/[/\\]/).pop() || item.uri);
      const match = findMatchingFile(item.uri, localAssets, preferExt);
      if (match) {
        const base = path.basename(match);
        ensureFileBesideGltf(match, base, gltfDir);
        if (base !== raw) {
          ensureFileBesideGltf(match, raw, gltfDir);
          console.log(`Bound: ${raw} ← ${base}`);
        }
        item.uri = raw;
        continue;
      }

      const dest = path.join(gltfDir, raw);
      if (!fs.existsSync(dest) && placeholder) {
        fs.writeFileSync(dest, placeholder);
        console.warn(`Missing ${raw} — placeholder`);
        item.uri = raw;
      }
    }
  };

  fixUriList(doc.images, null, PLACEHOLDER_PNG);
  fixUriList(doc.buffers, ".bin", null);

  if (doc.buffers) {
    for (const buf of doc.buffers) {
      if (!buf.uri || buf.uri.startsWith("data:")) continue;
      const raw = decodeURIComponent(buf.uri.split(/[/\\]/).pop() || buf.uri);
      const dest = path.join(gltfDir, raw);
      if (fs.existsSync(dest)) continue;
      const anyBin = localAssets.find((f) => f.toLowerCase().endsWith(".bin"));
      if (anyBin) {
        fs.copyFileSync(anyBin, dest);
        buf.uri = raw;
        console.log(`Bound buffer: ${raw} ← ${path.basename(anyBin)}`);
        continue;
      }
      const listing = listFiles(gltfDir).join("\n  ");
      throw new Error(
        `Нет файла геометрии .bin (нужен "${raw}").\n` +
          `Папка pack:\n  ${listing || "(пусто)"}\n` +
          `Скачайте .bin рядом с .gltf, либо экспортируйте .glb из Blender.`,
      );
    }
  }

  const fixedPath = path.join(gltfDir, "model.fixed.gltf");
  fs.writeFileSync(fixedPath, JSON.stringify(doc));
  console.log(`Prepared GLTF → ${fixedPath}`);
  return fixedPath;
}

function buildOptimizedGlb(inputPath, outputPath) {
  const q = (p) => `"${p}"`;
  const attempts = [
    `--compress meshopt --texture-compress webp`,
    `--compress meshopt --texture-compress false`,
  ];
  for (const flags of attempts) {
    try {
      run(`npx --yes @gltf-transform/cli optimize ${q(inputPath)} ${q(outputPath)} ${flags}`);
      return true;
    } catch {
      console.warn(`optimize failed (${flags}) — retrying...`);
    }
  }
  try {
    run(`npx --yes @gltf-transform/cli copy ${q(inputPath)} ${q(outputPath)}`);
    return true;
  } catch {
    console.warn("gltf-transform unavailable — keeping existing model.");
    return false;
  }
}

async function downloadFallback() {
  fs.mkdirSync(outDir, { recursive: true });
  const res = await fetch(fallbackUrl);
  if (!res.ok) throw new Error(`Fallback download failed: ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  fs.writeFileSync(outFile, buf);
  console.log(`Fallback avatar → ${outFile} (${(buf.length / 1e6).toFixed(1)} MB)`);
}

async function main() {
  const asset = findInputAsset();

  if (!asset) {
    if (fs.existsSync(outFile) && fs.statSync(outFile).size > 0) {
      const mb = fs.statSync(outFile).size / 1e6;
      console.log(`No custom source — using committed ${path.basename(outFile)} (${mb.toFixed(1)} MB)`);
      return;
    }
    console.warn("No model in pack/ and no committed GLB — downloading fallback...");
    await downloadFallback();
    return;
  }

  console.log(`Input: ${asset.path}`);
  try {
    unzipAllZips(asset.dir);
    const inputPath =
      asset.kind === "gltf" ? prepareGltfAssets(asset.path, asset.dir) : asset.path;

    fs.mkdirSync(outDir, { recursive: true });
    const tmp = path.join(outDir, "child-boy-raw.glb");
    if (!buildOptimizedGlb(inputPath, tmp)) throw new Error("GLB build failed");

    fs.renameSync(tmp, outFile);
    const mb = fs.statSync(outFile).size / 1e6;
    console.log(`Built ${outFile} (${mb.toFixed(1)} MB)`);
  } catch (err) {
    console.warn(`\n⚠️  Не удалось собрать модель из pack/: ${err.message}`);
    if (fs.existsSync(outFile) && fs.statSync(outFile).size > 0) {
      console.warn("Использую ранее собранную модель — сборка сайта продолжится.\n");
      return;
    }
    console.warn("Скачиваю запасной аватар...\n");
    await downloadFallback();
  }
}

main().catch((e) => {
  console.error(e);
  // Never break the site build over an optional 3D asset.
  if (fs.existsSync(outFile) && fs.statSync(outFile).size > 0) {
    console.warn("Оставляю существующий child-boy.glb.");
    process.exit(0);
  }
  process.exit(1);
});
