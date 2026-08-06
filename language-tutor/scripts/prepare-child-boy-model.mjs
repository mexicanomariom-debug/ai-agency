/**
 * Build webapp/public/models/child-boy.glb from CGTrader source files.
 *
 * Place in language-tutor/assets/child-boy/source/:
 *   - young boy character riigged.gltf (or any *.gltf)
 *   - textures.zip
 *   - optional: .blend / .fbx (not used by this script)
 *
 * Usage: node scripts/prepare-child-boy-model.mjs
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDir = path.join(root, "assets", "child-boy", "source");
const outDir = path.join(root, "webapp", "public", "models");
const outFile = path.join(outDir, "child-boy.glb");
const fallbackUrl =
  "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@main/avatars/vroid.glb";

function run(cmd) {
  console.log(cmd);
  execSync(cmd, { stdio: "inherit", cwd: root });
}

function findGltf(dir) {
  if (!fs.existsSync(dir)) return null;
  const names = fs.readdirSync(dir);
  const hit = names.find((n) => n.toLowerCase().endsWith(".gltf"));
  return hit ? path.join(dir, hit) : null;
}

function unzipTextures(dir) {
  const zip = path.join(dir, "textures.zip");
  if (!fs.existsSync(zip)) return;
  run(`unzip -o -q "${zip}" -d "${dir}"`);
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
  const gltf = findGltf(sourceDir);
  if (!gltf) {
    console.warn("No .gltf in assets/child-boy/source — using TalkingHead vroid fallback.");
    await downloadFallback();
    return;
  }

  unzipTextures(sourceDir);
  fs.mkdirSync(outDir, { recursive: true });
  const tmp = path.join(outDir, "child-boy-raw.glb");
  run(
    `npx --yes @gltf-transform/cli copy "${gltf}" "${tmp}" --compress meshopt --texture-compress webp`,
  );
  fs.renameSync(tmp, outFile);
  const mb = fs.statSync(outFile).size / 1e6;
  console.log(`Built ${outFile} (${mb.toFixed(1)} MB)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
