// Fails when a contract schema changes in a breaking way without a schemaVersion bump (KAN-7).
//
//   node breaking-check.mjs [--base origin/main]
//
// Compares every contracts/schemas/**/*.schema.json in the working tree with the same file
// on the base git ref. Breaking (fails unless the schema's schemaVersion const went up):
//   * a property removed
//   * a property newly required (an optional one made required, or a new required one)
//   * a type changed or narrowed
//   * an enum value removed, or a const changed
//   * a $ref pointing somewhere else
//   * a string/number/array limit tightened, or a pattern changed
//   * a schema file deleted
// Allowed: new optional properties, new enum values, new schema files, description changes.
//
// Schemas without a schemaVersion (common enums, HTTP bodies) cannot be bumped; a breaking
// change there means adding a new schema next to the old one instead.
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

const contractsDir = resolve(import.meta.dirname, "..");
const repoRoot = resolve(contractsDir, "..");
const schemasDir = join(contractsDir, "schemas");
const baseArg = process.argv.indexOf("--base");
const base = baseArg > -1 ? process.argv[baseArg + 1] : "origin/main";

const git = (...args) => execFileSync("git", args, { cwd: repoRoot, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
const toPosix = (p) => p.replaceAll("\\", "/");

let baseFiles;
try {
  baseFiles = git("ls-tree", "-r", "--name-only", base, "--", "contracts/schemas")
    .split("\n")
    .filter((f) => f.endsWith(".schema.json"));
} catch {
  console.error(`Cannot read git ref "${base}". Fetch it first (git fetch origin main).`);
  process.exit(2);
}

const walk = (dir) =>
  existsSync(dir)
    ? readdirSync(dir).flatMap((e) => {
        const p = join(dir, e);
        return statSync(p).isDirectory() ? walk(p) : [p];
      })
    : [];
const headFiles = new Map(
  walk(schemasDir)
    .filter((f) => f.endsWith(".schema.json"))
    .map((f) => [toPosix(relative(repoRoot, f)), f]),
);

const problems = [];

// Resolves the effective `schemaVersion` const of a schema, following one $ref if needed.
function schemaVersionOf(schema, file, loader) {
  const prop = schema?.properties?.schemaVersion;
  if (!prop) return null;
  if ("const" in prop) return prop.const;
  if (prop.$ref) {
    const [path, frag = ""] = prop.$ref.split("#");
    const target = loader(toPosix(join(dirname(file), path)));
    const node = frag.split("/").filter(Boolean).reduce((n, k) => n?.[k], target);
    return node?.const ?? null;
  }
  return null;
}

const asArray = (t) => (t === undefined ? [] : Array.isArray(t) ? t : [t]);
const TIGHTER = { maxLength: "lower", maxItems: "lower", maximum: "lower", minLength: "higher", minItems: "higher", minimum: "higher" };

// Local refs ("#/$defs/x") are replaced by their target before comparing, so moving a
// definition into $defs is not reported as a change. `roots` holds the two documents.
let roots = { old: null, new: null };
function local(node, root, depth = 0) {
  if (!node || typeof node !== "object" || typeof node.$ref !== "string" || !node.$ref.startsWith("#") || depth > 20) return node;
  const target = node.$ref
    .slice(1)
    .split("/")
    .filter(Boolean)
    .reduce((n, k) => n?.[k.replaceAll("~1", "/").replaceAll("~0", "~")], root);
  const { $ref, ...rest } = node;
  return local({ ...target, ...rest }, root, depth + 1);
}

function compare(oldS, newS, path, out) {
  oldS = local(oldS, roots.old);
  newS = local(newS, roots.new);
  if (!oldS || typeof oldS !== "object") return;
  if (!newS || typeof newS !== "object") {
    out.push(`${path}: removed`);
    return;
  }
  if ((oldS.$ref ?? null) !== (newS.$ref ?? null) && oldS.$ref) out.push(`${path}: $ref changed from ${oldS.$ref} to ${newS.$ref ?? "(none)"}`);

  const oldT = asArray(oldS.type);
  const newT = asArray(newS.type);
  if (oldT.length && (!newT.length ? false : oldT.some((t) => !newT.includes(t) && !(t === "integer" && newT.includes("number")))))
    out.push(`${path}: type changed from ${oldT.join("|")} to ${newT.join("|")}`);

  if (Array.isArray(oldS.enum)) {
    const removed = oldS.enum.filter((v) => !(newS.enum ?? []).includes(v));
    if (!newS.enum) out.push(`${path}: enum removed`);
    else if (removed.length) out.push(`${path}: enum value(s) removed: ${removed.join(", ")}`);
  }
  if ("const" in oldS && JSON.stringify(oldS.const) !== JSON.stringify(newS.const) && !path.endsWith("/schemaVersion"))
    out.push(`${path}: const changed from ${JSON.stringify(oldS.const)} to ${JSON.stringify(newS.const)}`);
  if (oldS.pattern !== undefined && oldS.pattern !== newS.pattern) out.push(`${path}: pattern changed`);
  if (oldS.pattern === undefined && newS.pattern !== undefined) out.push(`${path}: pattern added`);
  for (const [key, dir] of Object.entries(TIGHTER)) {
    const o = oldS[key];
    const n = newS[key];
    if (n === undefined) continue;
    if (o === undefined || (dir === "lower" ? n < o : n > o)) out.push(`${path}: ${key} tightened (${o ?? "none"} -> ${n})`);
  }
  if (oldS.additionalProperties !== false && newS.additionalProperties === false) out.push(`${path}: now rejects unknown properties`);

  const oldReq = new Set(oldS.required ?? []);
  for (const r of newS.required ?? []) if (!oldReq.has(r)) out.push(`${path}: "${r}" is now required`);

  for (const [name, sub] of Object.entries(oldS.properties ?? {})) {
    if (!newS.properties || !(name in newS.properties)) out.push(`${path}/properties/${name}: property removed`);
    else compare(sub, newS.properties[name], `${path}/properties/${name}`, out);
  }
  for (const [name, sub] of Object.entries(oldS.$defs ?? {})) {
    if (!newS.$defs || !(name in newS.$defs)) out.push(`${path}/$defs/${name}: definition removed`);
    else compare(sub, newS.$defs[name], `${path}/$defs/${name}`, out);
  }
  if (oldS.items) compare(oldS.items, newS.items, `${path}/items`, out);
  for (const key of ["allOf", "anyOf", "oneOf", "prefixItems"]) {
    (oldS[key] ?? []).forEach((sub, i) => compare(sub, newS[key]?.[i], `${path}/${key}/${i}`, out));
  }
  for (const key of ["if", "then", "else", "not"]) if (oldS[key]) compare(oldS[key], newS[key], `${path}/${key}`, out);
}

const loadBase = (p) => {
  try {
    return JSON.parse(git("show", `${base}:${p}`));
  } catch {
    return null;
  }
};
const loadHead = (p) => (headFiles.has(p) ? JSON.parse(readFileSync(headFiles.get(p), "utf8")) : null);

for (const file of baseFiles) {
  const oldS = loadBase(file);
  const newS = loadHead(file);
  if (!newS) {
    problems.push(`${file}: schema file deleted`);
    continue;
  }
  const changes = [];
  roots = { old: oldS, new: newS };
  compare(oldS, newS, "", changes);
  if (!changes.length) continue;
  const oldV = schemaVersionOf(oldS, file, loadBase);
  const newV = schemaVersionOf(newS, file, loadHead);
  if (oldV !== null && newV !== null && newV > oldV) {
    console.log(`  ok     ${file}: breaking changes with schemaVersion ${oldV} -> ${newV}`);
    continue;
  }
  for (const c of changes) problems.push(c.startsWith(":") ? `${file}${c}` : `${file}#${c}`);
}

const added = [...headFiles.keys()].filter((f) => !baseFiles.includes(f));
console.log(`Compared ${baseFiles.length} schema(s) with ${base}; ${added.length} new.`);
if (problems.length) {
  console.error("\nBreaking contract changes without a schemaVersion bump:");
  for (const p of problems) console.error(`  BREAKING  ${p}`);
  console.error("\nRaise schemaVersion (see contracts/README.md, 'Changing a contract') or make the change compatible.");
  process.exit(1);
}
console.log("No breaking changes.");
