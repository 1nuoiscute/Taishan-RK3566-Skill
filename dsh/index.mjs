import { readFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

export const name = 'dsh-taishan-rk3566';
export const inject = ['skills'];
export const displayName = '泰山派 RK3566 电赛视觉';
export const description = '按需加载泰山派视觉工作流、参考资料、模板和板端探针。';

const resourceRoot = fileURLToPath(new URL('../', import.meta.url));
const skillPath = fileURLToPath(new URL('./SKILL.md', import.meta.url));
const providerName = 'dsh-taishan-rk3566';

// This entry is generated from the repository's single-line frontmatter template.
function parseEntry(raw) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(raw);
  const skillName = match?.[1].match(/^name: ([a-z0-9-]+)$/mu)?.[1];
  const skillDescription = match?.[1].match(/^description: (.+)$/mu)?.[1];
  if (skillName !== 'taishan-rk3566' || !skillDescription) {
    throw new Error('dsh-taishan-rk3566: invalid generated Skill entry');
  }
  return { description: skillDescription, content: raw.slice(match[0].length).trim() };
}

/** Supply one packaged skill; Cordis owns unregistering it on plugin disposal. */
export function apply(ctx) {
  const entry = parseEntry(readFileSync(skillPath, 'utf8'));
  const version = readFileSync(new URL('../VERSION', import.meta.url), 'utf8').trim();
  const candidate = Object.freeze({
    name: 'taishan-rk3566',
    description: entry.description,
    invocation: Object.freeze({ modelInvocable: true, userInvocable: true }),
    provider: providerName,
    source: 'bundled',
    rank: 600,
    path: skillPath,
    resourceBase: Object.freeze({ kind: 'directory', path: resourceRoot }),
    metadata: Object.freeze({ version }),
    locator: skillPath,
  });
  ctx.skills.registerProvider(() => ({
    name: providerName,
    list: async (options = {}) => {
      options.signal?.throwIfAborted();
      return [candidate];
    },
    get: async (selected, options = {}) => {
      if (selected !== candidate) return undefined;
      const raw = await readFile(skillPath, { encoding: 'utf8', signal: options.signal });
      const { rank, locator, ...summary } = candidate;
      return { ...summary, ...parseEntry(raw) };
    },
  }));
}
