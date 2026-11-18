import { copyFile, mkdir } from "node:fs/promises";

const frontendRoot = new URL("../", import.meta.url);
const outputDirectory = new URL("assets/fonts/", frontendRoot);
const fontFiles = [
  ["@fontsource-variable/inter/files/inter-latin-wght-normal.woff2", "inter-latin-wght-normal.woff2"],
  ["@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2", "ibm-plex-mono-latin-500-normal.woff2"],
  ["@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-600-normal.woff2", "ibm-plex-mono-latin-600-normal.woff2"],
  ["@fontsource-variable/inter/LICENSE", "Inter-LICENSE.txt"],
  ["@fontsource/ibm-plex-mono/LICENSE", "IBM-Plex-Mono-LICENSE.txt"],
];

await mkdir(outputDirectory, { recursive: true });

for (const [source, filename] of fontFiles) {
  await copyFile(
    new URL(`node_modules/${source}`, frontendRoot),
    new URL(filename, outputDirectory),
  );
}
