import { readFileSync, writeFileSync } from "node:fs";

const packagePath = "/app/node_modules/@ctrl/qbittorrent/package.json";
const clientPath = "/app/node_modules/@ctrl/qbittorrent/dist/src/qbittorrent.js";
const packageMetadata = JSON.parse(readFileSync(packagePath, "utf8"));

if (packageMetadata.version !== "6.1.0") {
  throw new Error(
    `Unsupported @ctrl/qbittorrent version ${packageMetadata.version}; expected 6.1.0`,
  );
}

let source = readFileSync(clientPath, "utf8");
const replacements = [
  [
    "        if (!cookie || cookie.key !== 'SID') {\n            throw new Error('Invalid cookie');\n        }\n        this._sid = cookie.value;",
    "        if (!cookie || !cookie.value) {\n            throw new Error('Invalid cookie');\n        }\n        this._cookieName = cookie.key;\n        this._sid = cookie.value;",
  ],
  [
    "    logout() {\n        this._sid = undefined;",
    "    logout() {\n        this._cookieName = undefined;\n        this._sid = undefined;",
  ],
  [
    "                Cookie: `SID=${this._sid ?? ''}`",
    "                Cookie: `${this._cookieName ?? 'SID'}=${this._sid ?? ''}`",
  ],
];

for (const [before, after] of replacements) {
  const occurrences = source.split(before).length - 1;
  if (occurrences !== 1) {
    throw new Error(`Expected one patch target, found ${occurrences}`);
  }
  source = source.replace(before, after);
}

writeFileSync(clientPath, source);
