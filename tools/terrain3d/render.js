// v7.4.0 전쟁사 구상 컷 B(back_and_forth D-0604 §1-B) — 고도 높이맵 3D 궤도 렌더(headless Chromium + three.js 0.170.0, MIT).
// node render.js <scene_dir>  — scene_dir/scene.json·height.json·texture.png 를 읽어 scene_dir/frames/f_0000.png … 를 쓴다(text_in_engine 이면 frames/labels.json 도).
// 결정적: 무작위 없음, 프레임마다 카메라 방위만 scene.json 의 목록대로(고정 조명·고정 곡선). 수치는 scene.json(= rules sketch.war.terrain3d).
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const sceneDir = path.resolve(process.argv[2]);
const here = __dirname;
const types = { '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.html': 'text/html' };

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = u.startsWith('/three/') ? path.join(here, 'node_modules', 'three', u.slice(7))
    : u.startsWith('/scene/') ? path.join(sceneDir, u.slice(7)) : path.join(here, u);
  fs.readFile(f, (e, d) => {
    if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' });
    res.end(d);
  });
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const scene = JSON.parse(fs.readFileSync(path.join(sceneDir, 'scene.json')));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: scene.width, height: scene.height }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/view.html`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  fs.mkdirSync(path.join(sceneDir, 'frames'), { recursive: true });
  const labels = [];
  for (let i = 0; i < scene.frames.length; i++) {
    labels.push(await page.evaluate(fr => window.__draw(fr), scene.frames[i]));
    await page.screenshot({ path: path.join(sceneDir, 'frames', `f_${String(i).padStart(4, '0')}.png`) });
  }
  // 본편(scene.text_in_engine) — 프레임마다 라벨 화면 좌표(엔진이 글자·병종 그림을 그린다, back_and_forth D-0614 ①)
  if (scene.text_in_engine) fs.writeFileSync(path.join(sceneDir, 'frames', 'labels.json'), JSON.stringify({ schema_version: 1, frames: labels }));
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
