import fs from 'node:fs/promises';
import path from 'node:path';

const containerExecutableNames = ['libreoffice', 'soffice'];

export function getPathCandidates(envPath = process.env.PATH ?? '') {
  const delimiter = path.delimiter === ':' || !envPath.includes(':') ? path.delimiter : ':';
  return envPath
    .split(delimiter)
    .filter(Boolean)
    .flatMap((dir) => containerExecutableNames.map((name) => (
      dir.includes('/') ? path.posix.join(dir, name) : path.join(dir, name)
    )));
}

async function executable(file, access = fs.access) {
  try {
    await access(file, fs.constants.X_OK);
    return true;
  } catch {
    try {
      await access(file);
      return true;
    } catch {
      return false;
    }
  }
}

export async function findLibreOffice(options = {}) {
  const candidates = options.pathCandidates ?? getPathCandidates(options.envPath);
  const seen = new Set();
  for (const candidate of candidates) {
    if (seen.has(candidate)) continue;
    seen.add(candidate);
    if (await executable(candidate, options.access)) {
      return { found: true, path: candidate, candidates: [...seen] };
    }
  }
  return { found: false, path: null, candidates: [...seen] };
}

export function createLibreOfficeLocator(options = {}) {
  let cached;
  return async () => cached ??= await findLibreOffice(options);
}
