// Generates typed code from contracts/schemas (KAN-7).
//
//   node generate-types.mjs            write the generated files
//   node generate-types.mjs --check    fail if the committed files are out of date
//
// Outputs (committed, never edited by hand):
//   packages/contract-types-ts/src/index.ts                         TypeScript types (json-schema-to-typescript)
//   services/_shared/python/proofolio_contracts/models.py           Pydantic v2 models (datamodel-code-generator)
//
// Both are generated from one "bundle" schema that points at every schema file, so each
// shared type (ErrorCode, JobStatus, ...) is emitted once instead of once per file.
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, relative, resolve } from "node:path";
import { compile } from "json-schema-to-typescript";

const here = import.meta.dirname;
const contractsDir = resolve(here, "..");
const repoRoot = resolve(contractsDir, "..");
const schemasDir = join(contractsDir, "schemas");
const tsOut = join(repoRoot, "packages", "contract-types-ts", "src", "index.ts");
const pyOut = join(repoRoot, "services", "_shared", "python", "proofolio_contracts", "models.py");
const check = process.argv.includes("--check");

const HEADER = [
  "GENERATED FILE - DO NOT EDIT.",
  "Source: contracts/schemas. Regenerate with `make contracts-types`",
  "(or `npm run types` in contracts/tooling).",
];

const walk = (dir) =>
  readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });

// --- 1. Bundle: every schema file becomes one $defs entry named by its title. -----------
// Cross-file $refs are rewritten to point inside the bundle: a ref to a titled schema
// (an enum such as ErrorCode) becomes "#/$defs/ErrorCode" so it is emitted once; a ref to a
// shared field type (common/fields.schema.json#/$defs/...) is inlined, so generated fields
// carry their constraints directly instead of wrapper classes.
const files = walk(schemasDir)
  .filter((f) => f.endsWith(".schema.json"))
  .sort();
const byPath = new Map(files.map((f) => [resolve(f), JSON.parse(readFileSync(f, "utf8"))]));

const pointer = (doc, ptr) =>
  ptr
    .replace(/^#\/?/, "")
    .split("/")
    .filter(Boolean)
    .reduce((node, key) => node[key.replaceAll("~1", "/").replaceAll("~0", "~")], doc);

function rewrite(node, fromFile) {
  if (Array.isArray(node)) return node.map((n) => rewrite(n, fromFile));
  if (!node || typeof node !== "object") return node;
  const out = {};
  for (const [key, value] of Object.entries(node)) {
    if (key === "$ref" && typeof value === "string" && !value.startsWith("#")) {
      const [path, frag = ""] = value.split("#");
      const target = resolve(dirname(fromFile), path);
      const doc = byPath.get(target);
      if (!doc) throw new Error(`${relative(schemasDir, fromFile)}: cannot resolve $ref ${value}`);
      if (!frag && doc.title) {
        out.$ref = `#/$defs/${doc.title}`;
      } else {
        // Inline the referenced definition (and keep rewriting inside it).
        Object.assign(out, rewrite(frag ? pointer(doc, frag) : doc, target));
      }
    } else if (!["$schema", "$id", "x-queue"].includes(key)) {
      out[key] = rewrite(value, fromFile);
    }
  }
  return out;
}

const defs = {};
for (const [file, schema] of byPath) {
  if (!schema.title || schema.$defs && !schema.type) continue; // common/fields only holds $defs
  if (defs[schema.title]) throw new Error(`Two schemas share the title "${schema.title}"`);
  defs[schema.title] = rewrite(schema, file);
}
const ordered = Object.fromEntries(Object.entries(defs).sort(([a], [b]) => a.localeCompare(b)));
const bundle = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  title: "ProofolioContracts",
  type: "object",
  $defs: ordered,
};
const bundlePath = join(tmpdir(), `proofolio-bundle-${process.pid}.schema.json`);
writeFileSync(bundlePath, JSON.stringify(bundle, null, 2));

const outputs = {};
try {
  // --- 2. TypeScript. -------------------------------------------------------------------
  const ts = await compile(structuredClone(bundle), "ProofolioContracts", {
    bannerComment: `/* eslint-disable */\n/**\n * ${HEADER.join("\n * ")}\n */`,
    unreachableDefinitions: true,
    additionalProperties: false,
    strictIndexSignatures: true,
    format: true,
    style: { singleQuote: false, semi: true, printWidth: 100 },
  });
  // The bundle object itself is not a real contract: drop its empty interface.
  // Also drop the generator's "referenced by ProofolioContracts" boilerplate from each comment.
  outputs[tsOut] = ts
    .replace(/export interface ProofolioContracts \{[^}]*\}\n\n?/, "")
    .replace(/\/\*\*\n \* This interface was referenced by `ProofolioContracts`'s JSON-Schema\n \* via the `definition` "\w+"\.\n \*\/\n/g, "")
    .replace(/\n \*\n \* This interface was referenced by `ProofolioContracts`'s JSON-Schema\n \* via the `definition` "\w+"\./g, "");

  // --- 3. Python (Pydantic v2). -----------------------------------------------------------
  const python = process.env.PROOFOLIO_CODEGEN_PYTHON ?? findPython();
  const tmp = join(tmpdir(), `proofolio-models-${process.pid}.py`);
  execFileSync(
    python,
    [
      "-m", "datamodel_code_generator",
      "--input", bundlePath,
      "--input-file-type", "jsonschema",
      "--output", tmp,
      "--output-model-type", "pydantic_v2.BaseModel",
      "--target-python-version", "3.12",
      "--formatters", "black", "isort",
      "--class-name", "ProofolioContracts",
      "--use-standard-collections",
      "--use-union-operator",
      "--use-subclass-enum",
      "--field-constraints",
      "--disable-timestamp",
      "--custom-file-header", HEADER.map((l) => `# ${l}`).join("\n"),
    ],
    // Pydantic cannot express a regex on datetime/URL fields; the generator warns about it.
    // That is expected: JSON Schema validation (validate.mjs, or jsonschema in Python)
    // remains the full check, the models are for typing and parsing.
    { stdio: ["ignore", "inherit", "inherit"], env: { ...process.env, PYTHONWARNINGS: "ignore" } },
  );
  outputs[pyOut] = readFileSync(tmp, "utf8").replace(/\r\n/g, "\n");
  rmSync(tmp);
} finally {
  rmSync(bundlePath, { force: true });
}

// --- 4. Write or check. ---------------------------------------------------------------------
let stale = 0;
for (const [path, content] of Object.entries(outputs)) {
  const rel = relative(repoRoot, path);
  const current = existsSync(path) ? readFileSync(path, "utf8").replace(/\r\n/g, "\n") : null;
  if (check) {
    if (current !== content) {
      stale += 1;
      console.error(`  STALE  ${rel}`);
    } else console.log(`  ok     ${rel}`);
  } else {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, content);
    console.log(`  wrote  ${rel}`);
  }
}
if (stale) {
  console.error("\nGenerated types are out of date. Run `make contracts-types` and commit the result.");
  process.exit(1);
}

function findPython() {
  const venv = join(here, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
  if (existsSync(venv)) return venv;
  return process.platform === "win32" ? "python" : "python3";
}
