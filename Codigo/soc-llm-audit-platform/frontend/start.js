import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { execSync } from 'child_process';
const __dirname = dirname(fileURLToPath(import.meta.url));
process.chdir(__dirname);
execSync('node node_modules/vite/bin/vite.js --port 3000', {stdio: 'inherit'});
