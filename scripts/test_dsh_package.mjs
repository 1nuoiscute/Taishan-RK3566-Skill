import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { Context } from '@deepseek-ai/cordis';
import SkillRegistry, { renderSkillContent } from '@deepseek-ai/dsh-skill';

const packageRoot = resolve(process.argv[2]);
const sourceRoot = fileURLToPath(new URL('../', import.meta.url));
for (const file of ['dsh/index.mjs', 'dsh/SKILL.md', 'VERSION', 'tests/test_probe_camera.py']) {
  assert.deepEqual(await readFile(join(packageRoot, file)), await readFile(join(sourceRoot, file)), 'installed package is stale: ' + file);
}
const plugin = await import(pathToFileURL(join(packageRoot, 'dsh/index.mjs')));
const ctx = new Context();
ctx.plugin(SkillRegistry);
const fork = ctx.plugin(plugin);
await fork.await();
try {
  const skill = await ctx.skills.get('taishan-rk3566');
  assert.equal(resolve(skill.resourceBase.path), packageRoot);
  const rendered = renderSkillContent(skill);
  assert.ok(rendered.includes(packageRoot));
  for (const [, relative] of skill.content.matchAll(/\x60((?:references|templates)\/[^\x60]+)\x60/gu)) {
    assert.deepEqual(await readFile(join(packageRoot, relative)), await readFile(join(sourceRoot, relative)));
  }
  for (const script of ['probe_system.sh', 'probe_camera.py', 'probe_uart.py', 'probe_gpio.py', 'probe_rknn.py', 'run_baseline.sh']) {
    assert.deepEqual(await readFile(join(packageRoot, 'scripts', script)), await readFile(join(sourceRoot, 'scripts', script)));
  }
  await fork.dispose();
  assert.equal(await ctx.skills.get('taishan-rk3566'), undefined);
  console.log('packed-plugin registry, resources, and disposal verified');
} finally {
  await ctx.fiber.dispose();
}
