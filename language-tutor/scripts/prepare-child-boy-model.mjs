/**
 * Build webapp/public/models/child-boy.glb from CGTrader files in assets/child-boy/pack/
 *
 * Drop into pack/ (or source/):
 *   - *.gltf (required for custom model)
 *   - textures.zip (and any other *.zip with textures)
 *   - optional: .blend / .fbx (not converted by this script)
 *
 * Usage: node scripts/prepare-child-boy-model.mjs
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

function run(cmd) {
  console.log(cmd);
  execSync(cmd, { stdio: "inherit", cwd: root });
}

function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((n) => !n.startsWith("."));
}

function findAsset(dir) {
  if (!fs.existsSync(dir)) return null;
  const names = listFiles(dir);
  const gltf = names.find((n) => n.toLowerCase().endsWith(".gltf"));
  if (gltf) return { path: path.join(dir, gltf), kind: "gltf" };
  const glb = names.find((n) => n.toLowerCase().endsWith(".glb"));
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

function unzipAllZips(dir) {
  for (const name of listFiles(dir)) {
    if (name.toLowerCase().endsWith(".zip")) {
      run(`unzip -o -q "${path.join(dir, name)}" -d "${dir}"`);
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
  fs.mkdirSync(outDir, { recursive: true });
  const tmp = path.join(outDir, "child-boy-raw.glb");

  if (asset.kind === "glb" && asset.path !== outFile) {
    run(
      `npx --yes @gltf-transform/cli copy "${asset.path}" "${tmp}" --compress meshopt --texture-compress webp`,
    );
  } else {
    run(
      `npx --yes @gltf-transform/cli copy "${asset.path}" "${tmp}" --compress meshopt --texture-compress webp`,
    );
  }

  fs.renameSync(tmp, outFile);
  const mb = fs.statSync(outFile).size / 1e6;
  console.log(`Built ${outFile} (${mb.toFixed(1)} MB)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
