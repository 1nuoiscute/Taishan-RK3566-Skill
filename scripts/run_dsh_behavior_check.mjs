import { parseArgs } from 'node:util';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Developer-only: use an already authenticated, isolated SDK profile with this plugin installed.
const { values } = parseArgs({ options: {
  'sdk-module': { type: 'string' }, 'dsh-bin': { type: 'string' },
  home: { type: 'string' }, workspace: { type: 'string' }, output: { type: 'string' },
  scenarios: { type: 'string', default: 'R1,R2,R3,R4,R5,R6,R7' },
  model: { type: 'string', default: 'deepseek-flash' },
} });
for (const key of ['sdk-module', 'home', 'workspace', 'output']) {
  if (!values[key]) throw new Error('required option: --' + key);
}
const { DeepSeekHarness } = await import(pathToFileURL(resolve(values['sdk-module'])));
const root = fileURLToPath(new URL('../', import.meta.url));
const home = resolve(values.home), workspace = resolve(values.workspace), output = resolve(values.output);
await mkdir(output, { recursive: true });
const selected = new Set(values.scenarios.split(','));
const source = await readFile(join(root, 'references/validation-scenarios.md'), 'utf8');
const cases = source.split(/^### /mu).flatMap(section => {
  const id = /^(R[1-7])：/u.exec(section)?.[1];
  const input = /\x60{3}text\n([\s\S]*?)\n\x60{3}/u.exec(section)?.[1];
  return id && input && selected.has(id) ? [{ id, input }] : [];
});
if (cases.length !== selected.size) throw new Error('unknown or duplicate scenario selection');
const harness = new DeepSeekHarness({
  ...(values['dsh-bin'] ? { dshBin: resolve(values['dsh-bin']) } : {}),
  profile: 'sdk', dshHome: home, processCwd: workspace, cwd: workspace,
  provider: 'deepseek-official', model: values.model, maxTokens: 10000,
  initializeTimeoutMs: 30000, requestTimeoutMs: 180000,
});
let failed = false;
try {
  await harness.start();
  for (const { id, input } of cases) {
    const prompt = '请先加载 taishan-rk3566 技能。以下为合成场景，只做离线审查/方案；没有可连接的板端，不执行硬件探针、不修改文件、不发送串口数据。允许按需读取插件配套文件。若材料不足，明确待验证项。最终回答控制在约1000字，完整覆盖当前场景相关断言；不要联网搜索。\n\n'
      + input.replaceAll('$taishan-rk3566', 'taishan-rk3566')
      + '\n\n文件入口 scripts/probe_camera.py 等均指插件资源目录内现有文件；有需要先实际读取再分析。允许用 Python -B 运行配套 tests/test_probe_camera.py 纯假对象测试；它不接触硬件，也不写文件。';
    const result = await harness.run(prompt);
    const termination = result.events.findLast(e => e.type === 'turn/end')?.data.reason;
    // Keep raw results outside the public repository; review and redact paths before publishing.
    await writeFile(join(output, id + '.json'), JSON.stringify({ input: prompt, termination, ...result }, null, 2));
    const complete = termination?.kind === 'completed' && result.finalResponse.length > 0;
    failed ||= !complete;
    console.log(id + ': ' + JSON.stringify(termination) + ', final chars=' + result.finalResponse.length);
  }
} finally {
  await harness.close();
}
if (failed) process.exitCode = 1;
