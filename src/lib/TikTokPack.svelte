<script>
  import * as d3 from 'd3';
  import { fade } from 'svelte/transition';
  import { base } from '$app/paths';
  import data from '$lib/tiktok.json';
  import { COLORS } from '$lib/meta.js';

  // world = "Republican" (@whitehouse+@republicans) | "Democrat" (@democrats).
  // emotion = null (size by total posts) or an emotion key (size by that emotion).
  // colorBy = 'party' | 'lean'. monthIdx = null (all-time) or index into `months`.
  let { world = 'Republican', emotion = null, colorBy = 'party', monthIdx = null, months = [] } =
    $props();

  const ACCT_LABEL = { whitehouse: '@whitehouse', republicans: '@republicans', democrats: '@democrats' };
  const ATTACK = new Set(['mockery','contempt','outrage','anger','disgust','disapproval','ridicule','suspicion','fear','alarm','concern','sadness']);
  const HYPE = new Set(['pride','patriotism','admiration','triumph','inspiration','hope','celebration','confidence','strength','excitement','nostalgia','unity']);
  const emoColor = (e) => (ATTACK.has(e) ? '#8e44ad' : HYPE.has(e) ? '#2f9e6a' : '#9aa0a8');
  // attack↔hype lean (-1..+1) → purple..grey..green
  const leanScale = d3.scaleLinear().domain([-1, 0, 1]).range(['#8e44ad', '#c9ccd2', '#2f9e6a']).clamp(true);

  let all = $derived(data.children.find((c) => c.name === world).children);
  const val = (d) => {
    if (monthIdx !== null && months[monthIdx]) return d.monthly?.[months[monthIdx]] ?? 0; // that month's posts
    return emotion ? (d.emotions?.[emotion] ?? 0) : d.videos;
  };
  // when sizing by a month or an emotion, only show figures that actually have it
  let people = $derived(emotion || monthIdx !== null ? all.filter((d) => val(d) > 0) : all);

  let chartW = $state(0);
  let chartH = $state(0);
  let leaves = $derived.by(() => {
    if (chartW <= 0 || chartH <= 0 || people.length === 0) return [];
    const side = Math.min(chartW, chartH);
    const root = d3.hierarchy({ children: people }).sum((d) => val(d)).sort((a, b) => b.value - a.value);
    d3.pack().size([side, side]).padding(2)(root);
    const dx = (chartW - side) / 2, dy = (chartH - side) / 2;
    return root.leaves().map((n) => ({ d: n.data, x: n.x + dx, y: n.y + dy, r: n.r }));
  });

  const faceColor = (p) => (colorBy === 'lean' ? leanScale(p.lean ?? 0) : (COLORS[p.party] ?? '#8a8e97'));

  let hovered = $state(null);
  let tooltip = $state(null);
  let tipW = $state(236);
  let tipH = $state(240);
  function enter(node) {
    hovered = node.d.slug;
    tooltip = { x: node.x, y: node.y, r: node.r, person: node.d };
  }
  function leave() { hovered = null; tooltip = null; }
  // clamp the (measured) tooltip fully inside the chart: prefer above the circle,
  // else below, else beside — then hard-clamp to the viewport edges.
  let tipStyle = $derived.by(() => {
    if (!tooltip) return 'display:none';
    const { x, y, r } = tooltip;
    const w = tipW || 236, h = tipH || 240, m = 10;
    let left, top;
    if (y - r - h - m >= 8) {
      // room above → sit above the circle, centred, clamped horizontally
      left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, x));
      top = y - r - h - m;
    } else if (y + r + m + h <= chartH - 8) {
      // room below
      left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, x));
      top = y + r + m;
    } else {
      // big circle: tuck the card just BESIDE it (right edge if there's room, else
      // left), level with the face — adjacent but never over the centred face
      const roomRight = x + r + m + w <= chartW - 8;
      const cx = roomRight ? x + r + m + w / 2 : x - r - m - w / 2;
      left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, cx));
      top = Math.max(8, Math.min(chartH - h - 8, y - h / 2));
    }
    return `left:${left}px; top:${top}px`;
  });
</script>

<div class="wrap">
  <div class="chart" bind:clientWidth={chartW} bind:clientHeight={chartH}>
    {#if chartW > 0 && chartH > 0}
      <svg width={chartW} height={chartH} viewBox="0 0 {chartW} {chartH}" role="presentation">
        <defs>
          <clipPath id="ttClip" clipPathUnits="objectBoundingBox"><circle cx="0.5" cy="0.5" r="0.5" /></clipPath>
        </defs>
        {#each leaves as node (node.d.slug)}
          <g class="node" class:dim={hovered && hovered !== node.d.slug} class:on={hovered === node.d.slug}
            style="transform: translate({node.x}px, {node.y}px)"
            onmouseenter={() => enter(node)} onmouseleave={leave}
            in:fade={{ duration: 250 }} out:fade={{ duration: 200 }} role="presentation">
            <g class="bubble" style="transform: scale({node.r})">
              <circle class="ring" r="1" fill={faceColor(node.d)} />
              {#if node.d.img}
                <image href={base + node.d.img} x="-1" y="-1" width="2" height="2"
                  preserveAspectRatio="xMidYMid slice" clip-path="url(#ttClip)" />
              {/if}
              <circle class="stroke" r="1" fill="none" stroke={faceColor(node.d)} />
            </g>
          </g>
        {/each}
      </svg>

      {#if tooltip}
        {@const p = tooltip.person}
        {@const emos = Object.entries(p.emotions ?? {})}
        {@const emax = emos.length ? emos[0][1] : 1}
        {@const shownEmos =
          emotion && !emos.slice(0, 7).some(([e]) => e === emotion)
            ? [emos.find(([e]) => e === emotion) ?? [emotion, 0], ...emos.slice(0, 6)]
            : emos.slice(0, 7)}
        <div class="tip" bind:clientWidth={tipW} bind:clientHeight={tipH} style={tipStyle}>
          <div class="tip-name">{p.name}</div>
          <div class="tip-meta" style="color: {COLORS[p.party] ?? '#889'}">
            {p.party}{p.party !== world ? ' · opposition' : ''}
          </div>
          <div class="tip-big"><b>{p.videos}</b> post{p.videos === 1 ? '' : 's'}
            <span class="sub">· shown {p.shown} · named/implied {p.videos - p.shown}</span>
          </div>
          <div class="tip-lean">
            <span class="lean-lab" style="color:#8e44ad">attack</span>
            <div class="lean-track"><div class="lean-dot" style="left: {(( (p.lean ?? 0) + 1) / 2) * 100}%"></div></div>
            <span class="lean-lab" style="color:#2f9e6a">hype</span>
          </div>
          {#if emos.length}
            <div class="tip-section">emotions engineered {p.main ? `(as main character in ${p.main})` : ''}</div>
            <div class="emo-bars">
              {#each shownEmos as [e, n]}
                <div class="emo-row" class:hi={emotion === e}>
                  <span>{e}</span>
                  <div class="etrack"><div class="efill" style="width: {(n / emax) * 100}%; background: {emoColor(e)}"></div></div>
                  <b>{n}</b>
                </div>
              {/each}
            </div>
          {/if}
          {#if p.byAccount}
            <div class="tip-accts">
              {#each Object.entries(p.byAccount) as [acct, n]}<span>{ACCT_LABEL[acct] ?? acct}: <b>{n}</b></span>{/each}
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .wrap { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .chart { position: relative; flex: 1 1 auto; min-height: 0; width: 100%; }
  svg { display: block; width: 100%; height: 100%; }
  .node { transition: transform 600ms cubic-bezier(0.4,0,0.2,1), opacity 200ms ease; cursor: pointer; }
  .node.dim { opacity: 0.72; }
  .bubble { transition: transform 600ms cubic-bezier(0.4,0,0.2,1); }
  .ring { opacity: 0.28; }
  /* always-visible coloured border so "colour by" reads across the whole board */
  .stroke { stroke-width: 3; stroke-opacity: 1; vector-effect: non-scaling-stroke; }
  .node.on .stroke { stroke-width: 5; stroke-opacity: 1; vector-effect: non-scaling-stroke; }
  .tip { position: absolute; transform: translateX(-50%); width: 236px; background: #fff;
    border: 1px solid #e1e5ea; border-radius: 10px; padding: 0.6rem 0.75rem; box-shadow: 0 6px 22px rgba(0,0,0,0.15);
    pointer-events: none; z-index: 5; }
  .tip-name { font-weight: 700; font-size: 0.92rem; line-height: 1.2; }
  .tip-meta { font-size: 0.72rem; color: #99a; }
  .tip-big { margin: 0.4rem 0 0.3rem; font-size: 0.95rem; }
  .tip-big b { font-size: 1.1rem; }
  .tip-big .sub { font-size: 0.68rem; color: #99a; }
  .tip-lean { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 0.4rem; margin: 0.35rem 0 0.2rem; }
  .lean-lab { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .lean-track { position: relative; height: 6px; border-radius: 3px;
    background: linear-gradient(90deg, #8e44ad, #eceef1 50%, #2f9e6a); }
  .lean-dot { position: absolute; top: -2px; width: 10px; height: 10px; border-radius: 50%; background: #1f2933;
    border: 2px solid #fff; transform: translateX(-50%); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
  .tip-section { margin: 0.5rem 0 0.15rem; font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: #aab; }
  .emo-row { display: grid; grid-template-columns: 5rem 1fr 1.5rem; align-items: center; gap: 0.4rem;
    font-size: 0.7rem; margin-top: 0.15rem; }
  .emo-row span { color: #667; white-space: nowrap; text-transform: capitalize; }
  .emo-row b { text-align: right; }
  .emo-row.hi span, .emo-row.hi b { color: #1f2933; font-weight: 700; }
  .etrack { height: 6px; background: #eef0f3; border-radius: 3px; overflow: hidden; }
  .efill { height: 100%; border-radius: 3px; }
  .tip-accts { margin-top: 0.4rem; display: flex; flex-wrap: wrap; gap: 0.5rem; font-size: 0.7rem; color: #667; }
</style>
