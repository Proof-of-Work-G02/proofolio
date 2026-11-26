// Smoke test for the generated types (KAN-7): they import, and every valid example fits them.
//
//   node test-types.mjs
//
// TypeScript: writes a throwaway .ts file that assigns every valid example to its generated
//   type (`satisfies`) and type-checks it with tsc --strict.
// Python:     imports proofolio_contracts, parses every valid example with its Pydantic model,
//   and checks that the "missing-<field>" invalid examples are rejected.
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, relative, resolve } from "node:path";

const here = import.meta.dirname;
const contractsDir = resolve(here, "..");
const repoRoot = resolve(contractsDir, "..");
const walk = (dir) =>
  readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });

// schema name (file stem) -> generated type name (schema title)
const titles = new Map();
for (const f of walk(join(contractsDir, "schemas")).filter((f) => f.endsWith(".schema.json"))) {
  const s = JSON.parse(readFileSync(f, "utf8"));
  if (s.title && s.type === "object") titles.set(basename(f, ".schema.json"), s.title);
}
const examples = walk(join(contractsDir, "examples")).filter((f) => f.endsWith(".json"));
const valid = examples.filter((f) => !relative(contractsDir, f).includes("invalid") && titles.has(basename(f, ".json")));
const missing = examples
  .filter((f) => relative(contractsDir, f).includes("invalid") && /-missing-/.test(basename(f)))
  .map((f) => [f, [...titles.keys()].filter((n) => basename(f).startsWith(`${n}-`)).sort((a, b) => b.length - a.length)[0]])
  .filter(([, n]) => n);

// --- TypeScript ---------------------------------------------------------------------------
const tmp = mkdtempSync(join(tmpdir(), "proofolio-types-"));
try {
  const index = resolve(repoRoot, "packages/contract-types-ts/src/index.ts").replaceAll("\\", "/");
  const used = [...new Set(valid.map((f) => titles.get(basename(f, ".json"))))];
  const lines = [`import type { ${used.join(", ")} } from ${JSON.stringify(index.replace(/\.ts$/, ".js"))};`];
  valid.forEach((f, i) => {
    lines.push(`export const example${i} = ${readFileSync(f, "utf8").trim()} satisfies ${titles.get(basename(f, ".json"))};`);
  });
  writeFileSync(join(tmp, "smoke.ts"), lines.join("\n") + "\n");
  const tsc = join(here, "node_modules", "typescript", "bin", "tsc");
  execFileSync(
    process.execPath,
    [tsc, "--noEmit", "--strict", "--module", "nodenext", "--moduleResolution", "nodenext", "--target", "es2022",
     "--allowImportingTsExtensions", "false", join(tmp, "smoke.ts")],
    { stdio: "inherit" },
  );
  console.log(`  ok  TypeScript: ${valid.length} valid examples type-check against the generated types`);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

// --- Python -------------------------------------------------------------------------------
const venv = join(here, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.PROOFOLIO_CODEGEN_PYTHON ?? (existsSync(venv) ? venv : process.platform === "win32" ? "python" : "python3");
const script = `
import json, sys
import proofolio_contracts as pc
valid, missing = json.loads(sys.argv[1]), json.loads(sys.argv[2])
for path, title in valid:
    getattr(pc, title).model_validate(json.load(open(path, encoding="utf-8")))
bad = []
for path, title in missing:
    try:
        getattr(pc, title).model_validate(json.load(open(path, encoding="utf-8")))
        bad.append(path)
    except pc.ValidationError:
        pass
if bad:
    sys.exit("Accepted invalid examples: " + ", ".join(bad))
print(f"  ok  Python: {len(valid)} valid examples parse, {len(missing)} missing-field examples are rejected")
`;
execFileSync(
  python,
  [
    "-c", script,
    JSON.stringify(valid.map((f) => [f, titles.get(basename(f, ".json"))])),
    JSON.stringify(missing.map(([f, n]) => [f, titles.get(n)])),
  ],
  { stdio: "inherit", env: { ...process.env, PYTHONPATH: join(repoRoot, "services", "_shared", "python") } },
);
