import os from 'os';
// Allow the dev server to be opened from this computer's own network addresses (e.g. http://172.20.10.3:3001),
// not only http://localhost:3001. Without this, pages opened via the network address never finish loading.
const ips = Object.values(os.networkInterfaces()).flat().filter(i => i && i.family === 'IPv4').map(i => i.address);
const nextConfig = { allowedDevOrigins: [...new Set([...ips, 'localhost', '127.0.0.1'])] };
export default nextConfig;
