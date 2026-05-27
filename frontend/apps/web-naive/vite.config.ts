import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import process from 'node:process';

import { defineConfig } from '@vben/vite-config';

const certDir = resolve(process.cwd(), 'cert');
const certKeyPath = resolve(certDir, 'key.pem');
const certPath = resolve(certDir, 'cert.pem');
const gitignorePath = resolve(certDir, '.gitignore');

async function ensureDevCert() {
  if (existsSync(certKeyPath) && existsSync(certPath)) {
    return { cert: readFileSync(certPath), key: readFileSync(certKeyPath) };
  }

  // Collect all local IPv4 addresses for SAN
  const os = await import('node:os');
  const localIps = Object.values(os.networkInterfaces())
    .flat()
    .filter((i): i is NonNullable<typeof i> => i != null && i.family === 'IPv4' && !i.internal)
    .map((i) => i.address);

  const sanParts = ['DNS:localhost', 'IP:127.0.0.1', ...localIps.map((ip) => `IP:${ip}`)];
  const sanArg = sanParts.join(',');

  mkdirSync(certDir, { recursive: true });
  writeFileSync(gitignorePath, '*.pem\n', 'utf8');

  const cn = localIps[0] ?? 'localhost';
  execSync(
    `openssl req -x509 -newkey rsa:2048 -nodes -days 365 ` +
      `-keyout "${certKeyPath}" -out "${certPath}" ` +
      `-subj "/CN=${cn}" -addext "subjectAltName=${sanArg}"`,
    { stdio: 'pipe' },
  );

  console.log(`[dev-https] Self-signed cert generated for: ${sanParts.join(', ')}`);
  return { cert: readFileSync(certPath), key: readFileSync(certKeyPath) };
}

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        https: await ensureDevCert(),
        proxy: {
          '/api': {
            changeOrigin: true,
            target: 'http://localhost:8080',
            ws: true,
          },
        },
      },
    },
  };
});
