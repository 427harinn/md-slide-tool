import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
const winNames = ['soffice.exe', 'soffice.com', 'libreoffice.exe'];
export function getPlatformCandidates(platform = process.platform) {
  if (platform === 'win32') return [
    'C:\\Program Files\\LibreOffice\\program\\soffice.exe',
    'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe'
  ];
  if (platform === 'darwin') return [
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    path.join(os.homedir(), 'Applications/LibreOffice.app/Contents/MacOS/soffice')
  ];
  return ['soffice', 'libreoffice'];
}
export function getPathCandidates(envPath = process.env.PATH ?? '', platform = process.platform) {
  const names = platform === 'win32' ? winNames : ['soffice', 'libreoffice'];
  return envPath.split(path.delimiter).filter(Boolean).flatMap((dir) => names.map((name) => path.join(dir, name)));
}
async function executable(file, access = fs.access) { try { await access(file, fs.constants.X_OK); return true; } catch { try { await access(file); return true; } catch { return false; } } }
export async function findLibreOffice(options = {}) {
  const platform = options.platform ?? process.platform;
  const candidates = [...(options.pathCandidates ?? getPathCandidates(options.envPath, platform)), ...(options.platformCandidates ?? getPlatformCandidates(platform))];
  const seen = new Set();
  for (const candidate of candidates) { if (seen.has(candidate)) continue; seen.add(candidate); if (await executable(candidate, options.access)) return { found: true, path: candidate, candidates: [...seen] }; }
  return { found: false, path: null, candidates: [...seen] };
}
export function createLibreOfficeLocator(options = {}) { let cached; return async () => cached ??= await findLibreOffice(options); }
