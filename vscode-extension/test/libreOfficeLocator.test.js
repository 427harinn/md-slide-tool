import test from 'node:test';
import assert from 'node:assert/strict';
import { getPathCandidates, findLibreOffice } from '../src/preview/libreOfficeLocator.js';

test('PATH candidates use container libreoffice and soffice only', () => {
  assert.deepEqual(getPathCandidates(['/usr/bin', '/opt/bin'].join(':')), [
    '/usr/bin/libreoffice',
    '/usr/bin/soffice',
    '/opt/bin/libreoffice',
    '/opt/bin/soffice'
  ]);
});

test('findLibreOffice returns first executable PATH candidate and reports missing', async () => {
  const access = async (candidate) => {
    if (candidate !== '/usr/bin/libreoffice') throw new Error('no');
  };
  const found = await findLibreOffice({
    pathCandidates: ['/usr/bin/libreoffice', '/usr/bin/soffice'],
    access
  });
  assert.equal(found.path, '/usr/bin/libreoffice');

  const missing = await findLibreOffice({
    pathCandidates: ['/usr/bin/libreoffice', '/usr/bin/soffice'],
    access: async () => { throw new Error('no'); }
  });
  assert.equal(missing.found, false);
});
