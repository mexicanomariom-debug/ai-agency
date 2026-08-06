/**
 * Build webapp/public/models/child-boy.glb from CGTrader files in assets/child-boy/pack/
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

function findAsset(dir) {
  if (!fs.existsSync(dir)) return null;
  const names = listFiles(dir);
  const gltf = names.find((n) => n.toLowerCase().endsWith(".gltf"));
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

/** CGTrader zips often nest textures — copy images/bin next to .gltf and fix URIs. */
function prepareGltfAssets(gltfPath, searchRoot) {
  const gltfDir = path.dirname(gltfPath);
  const allFiles = walkFiles(searchRoot);
  const assets = allFiles.filter((f) => ASSET_EXT.test(f));

  for (const file of assets) {
    const base = path.basename(file);
    const dest = path.join(gltfDir, base);
    if (file !== dest && !fs.existsSync(dest)) {
      fs.copyFileSync(file, dest);
      console.log(`Copied: ${base}`);
    }
  }

  const byName = new Map(
    assets.map((f) => [path.basename(f).toLowerCase(), path.basename(f)]),
  );

  const resolveName = (uri) => {
    const raw = decodeURIComponent(uri.split(/[/\\]/).pop() || uri);
    if (byName.has(raw.toLowerCase())) return byName.get(raw.toLowerCase());
    const stem = raw.replace(/\.[^.]+$/, "").toLowerCase();
    for (const [low, name] of byName) {
      if (low.includes(stem) || stem.includes(low.replace(/\.[^.]+$/, ""))) return name;
    }
    return raw;
  };

  const doc = JSON.parse(fs.readFileSync(gltfPath, "utf8"));
  let changed = false;

  if (doc.images) {
    for (const img of doc.images) {
      if (!img.uri || img.uri.startsWith("data:")) continue;
      const fixed = resolveName(img.uri);
      if (fixed !== img.uri) {
        img.uri = fixed;
        changed = true;
      }
      const dest = path.join(gltfDir, fixed);
      if (!fs.existsSync(dest)) {
        const src = assets.find((f) => path.basename(f).toLowerCase() === fixed.toLowerCase());
        if (src) fs.copyFileSync(src, dest);
      }
      if (!fs.existsSync(dest)) {
        fs.writeFileSync(dest, PLACEHOLDER_PNG);
        console.warn(`Missing texture ${fixed} — 1×1 placeholder`);
        changed = true;
      }
    }
  }

  const fixedPath = path.join(gltfDir, "model.fixed.gltf");
  if (changed || !fs.existsSync(fixedPath)) {
    fs.writeFileSync(fixedPath, JSON.stringify(doc));
    console.log(`Prepared GLTF → ${fixedPath}`);
    return fixedPath;
  }
  return gltfPath;
}

function buildOptimizedGlb(inputPath, outputPath) {
  const q = (p) => `"${p}"`;
  try {
    run(
      `npx --yes @gltf-transform/cli optimize ${q(inputPath)} ${q(outputPath)} --compress meshopt --texture-compress webp`,
    );
  } catch {
    console.warn("WebP optimize failed — retrying without texture compression...");
    try {
      run(
        `npx --yes @gltf-transform/cli optimize ${q(inputPath)} ${q(outputPath)} --compress meshopt --texture-compress false`,
      );
    } catch {
      console.warn("Optimize failed — plain GLB copy...");
      run(`npx --yes @gltf-transform/cli copy ${q(inputPath)} ${q(outputPath)}`);
    }
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
    console.warn(
      "No .gltf/.glb in assets/child-boy/pack or source — using TalkingHead vroid fallback.",
    );
    await downloadFallback();
    return;
  }

  console.log(`Input: ${asset.path}`);
  unzipAllZips(asset.dir);

  let inputPath = asset.path;
  if (asset.kind === "gltf") {
    inputPath = prepareGltfAssets(asset.path, asset.dir);
  }

  fs.mkdirSync(outDir, { recursive: true });
  const tmp = path.join(outDir, "child-boy-raw.glb");
  buildOptimizedGlb(inputPath, tmp);

  fs.renameSync(tmp, outFile);
  const mb = fs.statSync(outFile).size / 1e6;
  console.log(`Built ${outFile} (${mb.toFixed(1)} MB)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
