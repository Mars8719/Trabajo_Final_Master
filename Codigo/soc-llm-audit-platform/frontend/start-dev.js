import { createServer } from 'vite';

const server = await createServer({
  configFile: './vite.config.ts',
  server: { port: 3000 }
});
await server.listen();
server.printUrls();
