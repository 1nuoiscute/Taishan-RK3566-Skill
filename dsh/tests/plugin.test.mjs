import assert from 'node:assert/strict';
import { readFile, mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { Context } from '@deepseek-ai/cordis';
import SkillRegistry, { renderSkillContent } from '@deepseek-ai/dsh-skill';
import * as filesystem from '@deepseek-ai/dsh-skill-filesystem';
import * as plugin from '../index.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
async function mount(t) {
  const ctx = new Context();
  ctx.plugin(SkillRegistry);
  const fork = ctx.plugin(plugin);
  await ctx.fiber.await();
  t.after(() => ctx.fiber.dispose());
  return { ctx, fork };
}

test('native registry discovers and loads the packaged skill and every routed resource', async (t) => {
  const { ctx } = await mount(t);
  const catalog = await ctx.skills.list({ cwd: tmpdir() });
  assert.equal(catalog.length, 1);
  assert.equal(catalog[0].name, 'taishan-rk3566');
  assert.equal(catalog[0].source, 'bundled');
  const skill = await ctx.skills.get('taishan-rk3566');
  assert.ok(skill.content.includes('DeepSeek Harness'));
  assert.equal(skill.invocation.modelInvocable, true);
  assert.equal(skill.invocation.userInvocable, true);
  assert.equal(resolve(skill.resourceBase.path), resolve(root));
  assert.ok(renderSkillContent(skill).includes(root));
  const resources = [...skill.content.matchAll(/\x60((?:references|templates)\/[^\x60]+)\x60/gu)].map(m => m[1]);
  assert.ok(resources.length >= 26);
  for (const resource of resources) assert.ok((await readFile(join(skill.resourceBase.path, resource), 'utf8')).length);
  for (const script of ['probe_system.sh', 'probe_camera.py', 'probe_uart.py', 'probe_gpio.py', 'probe_rknn.py', 'run_baseline.sh']) {
    assert.ok((await readFile(join(skill.resourceBase.path, 'scripts', script), 'utf8')).length);
  }
});

test('disposing and remounting removes and restores the catalog entry', async (t) => {
  const { ctx, fork } = await mount(t);
  assert.ok(await ctx.skills.get('taishan-rk3566'));
  await fork.dispose();
  assert.equal(await ctx.skills.get('taishan-rk3566'), undefined);
  assert.deepEqual(await ctx.skills.list(), []);
  ctx.plugin(plugin);
  await new Promise(resolve => setImmediate(resolve));
  assert.ok(await ctx.skills.get('taishan-rk3566'));
});

test('an existing local skill wins and removing it restores the packaged fallback', async (t) => {
  const temp = await mkdtemp(join(tmpdir(), 'taishan-dsh-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const skills = join(temp, 'skills');
  const local = join(skills, 'taishan-rk3566');
  await mkdir(local, { recursive: true });
  await writeFile(join(local, 'SKILL.md'), '---\nname: taishan-rk3566\ndescription: Local override\n---\nLocal content\n');
  const ctx = new Context();
  ctx.plugin(SkillRegistry);
  ctx.plugin(filesystem, { includeDefaultRoots: false, customSkillDirs: [skills], watch: false });
  ctx.plugin(plugin);
  await ctx.fiber.await();
  t.after(() => ctx.fiber.dispose());
  assert.equal((await ctx.skills.get('taishan-rk3566', { cwd: temp })).content.trim(), 'Local content');
  await rm(local, { recursive: true });
  ctx.skills.invalidateCache();
  assert.ok((await ctx.skills.get('taishan-rk3566', { cwd: temp })).content.includes('DeepSeek Harness'));
});

test('cancelled lookup is rejected and unrelated names remain absent', async (t) => {
  const { ctx } = await mount(t);
  const controller = new AbortController();
  controller.abort(new Error('cancelled'));
  await assert.rejects(ctx.skills.get('taishan-rk3566', { signal: controller.signal }), /cancelled/);
  assert.equal(await ctx.skills.get('unrelated-skill'), undefined);
});
