// Validates every contract example against its schema (KAN-7).
//
//   node validate.mjs [contractsDir]
//
// * Every *.schema.json under schemas/ must compile (strict JSON Schema 2020-12).
// * Every examples/**/<name>.json (outside invalid/) must pass the schema <name>.
// * Every examples/invalid/**/<name>-<case>.json must FAIL the schema <name>.
// An example's schema is the schema whose name is the longest prefix of the file name,
// so "website-draft-missing-id.json" maps to "website-draft", not "website".
import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { basename, join, relative, resolve, sep } from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import SwaggerParser from "@apidevtools/swagger-parser";

const contractsDir = resolve(process.argv[2] ?? join(import.meta.dirname, ".."));
const schemasDir = join(contractsDir, "schemas");
const examplesDir = join(contractsDir, "examples");

const walk = (dir) =>
  readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });

// strictRequired is off: `if/then: {required: [...]}` legitimately names properties that are
// defined on the parent object.
const ajv = new Ajv2020({ strict: true, strictRequired: false, allErrors: true });
addFormats(ajv);
ajv.addKeyword({ keyword: "x-queue", schemaType: "string" });

const schemaFiles = walk(schemasDir).filter((f) => f.endsWith(".schema.json"));
const schemas = new Map(); // name -> $id
let failures = 0;
const fail = (msg) => {
  failures += 1;
  console.error(`  FAIL  ${msg}`);
};

for (const file of schemaFiles) {
  const schema = JSON.parse(readFileSync(file, "utf8"));
  const name = basename(file, ".schema.json");
  if (!schema.$id) fail(`${relative(contractsDir, file)}: missing $id`);
  if (schemas.has(name)) fail(`${relative(contractsDir, file)}: duplicate schema name "${name}"`);
  schemas.set(name, schema.$id);
  ajv.addSchema(schema);
}

console.log(`Schemas (${schemaFiles.length}):`);
for (const [name, id] of schemas) {
  try {
    ajv.getSchema(id);
    console.log(`  ok    ${name}`);
  } catch (err) {
    fail(`${name}: does not compile: ${err.message}`);
  }
}

const schemaFor = (file) => {
  const stem = basename(file, ".json");
  let best = null;
  for (const name of schemas.keys()) {
    if ((stem === name || stem.startsWith(`${name}-`)) && (!best || name.length > best.length)) best = name;
  }
  return best;
};

let exampleFiles = [];
try {
  exampleFiles = walk(examplesDir).filter((f) => f.endsWith(".json"));
} catch {
  /* no examples yet */
}

console.log(`Examples (${exampleFiles.length}):`);
for (const file of exampleFiles.sort()) {
  const rel = relative(contractsDir, file);
  const invalid = relative(examplesDir, file).split(sep).includes("invalid");
  const name = schemaFor(file);
  if (!name) {
    fail(`${rel}: no schema matches this file name`);
    continue;
  }
  if (!invalid && basename(file, ".json") !== name) {
    fail(`${rel}: valid examples must be named exactly <schema>.json`);
    continue;
  }
  let validate;
  try {
    validate = ajv.getSchema(schemas.get(name));
  } catch {
    continue; // already reported as "does not compile"
  }
  if (!validate) continue;
  let data;
  try {
    data = JSON.parse(readFileSync(file, "utf8"));
  } catch (err) {
    fail(`${rel}: not valid JSON: ${err.message}`);
    continue;
  }
  const ok = validate(data);
  if (invalid && ok) fail(`${rel}: expected to FAIL ${name} but it passed`);
  else if (!invalid && !ok) fail(`${rel}: ${ajv.errorsText(validate.errors, { separator: "; " })}`);
  else console.log(`  ok    ${rel}${invalid ? `  (rejected: ${validate.errors[0].instancePath || "/"} ${validate.errors[0].message})` : ""}`);
}

// OpenAPI 3.1 documents (KAN-15): structurally valid, and every $ref (including the ones into
// ../schemas) resolves.
const openapiDir = join(contractsDir, "openapi");
if (existsSync(openapiDir)) {
  const docs = readdirSync(openapiDir).filter((f) => /\.ya?ml$|\.json$/.test(f)).sort();
  console.log(`OpenAPI (${docs.length}):`);
  for (const doc of docs) {
    try {
      await SwaggerParser.validate(join(openapiDir, doc), {
        resolve: {
          // Schema $ids look like URLs; map them back to the local files instead of downloading.
          http: false,
          contracts: {
            order: 1,
            canRead: /^https:\/\/proofolio\.dev\/contracts\//,
            read: (file) => readFileSync(join(contractsDir, file.url.replace("https://proofolio.dev/contracts/", "").split("#")[0])),
          },
        },
      });
      console.log(`  ok    openapi/${doc}`);
    } catch (err) {
      fail(`openapi/${doc}: ${err.message.split("\n")[0]}`);
    }
  }
}

// HMAC test vectors (KAN-15): each case must behave as its "expected" says when verified with
// the documented scheme, so the Python (BE-10) and Node (FE-33) verifiers can share them.
const vectorsFile = join(contractsDir, "hmac", "test-vectors.json");
if (existsSync(vectorsFile)) {
  const v = JSON.parse(readFileSync(vectorsFile, "utf8"));
  console.log(`HMAC test vectors (${v.cases.length}):`);
  for (const c of v.cases) {
    const h = c.request.headers;
    const canonical = [
      c.request.method.toUpperCase(),
      c.request.path,
      h["X-Service-Timestamp"],
      h["X-Actor-User-Id"] ?? "",
      createHash("sha256").update(c.request.body, "utf8").digest("hex"),
    ].join("\n");
    const expectedSig = Buffer.from(`v1=${createHmac("sha256", v.secret).update(canonical, "utf8").digest("hex")}`);
    const given = Buffer.from(h["X-Service-Signature"]);
    const sigOk = given.length === expectedSig.length && timingSafeEqual(given, expectedSig);
    const fresh = Math.abs(c.verifyAt - Number(h["X-Service-Timestamp"])) <= v.maxAgeSeconds;
    const outcome = !sigOk ? "invalid" : fresh ? "valid" : "expired";
    if (outcome !== c.expected) fail(`hmac/${c.name}: expected ${c.expected}, verifier says ${outcome}`);
    else if (c.canonicalString !== canonical) fail(`hmac/${c.name}: canonicalString does not match`);
    else console.log(`  ok    ${c.name} (${outcome})`);
  }
}

if (failures) {
  console.error(`\n${failures} problem(s).`);
  process.exit(1);
}
console.log("\nAll contracts valid.");
