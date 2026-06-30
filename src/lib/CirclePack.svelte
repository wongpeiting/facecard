<script>
  import * as d3 from 'd3';
  import { fade } from 'svelte/transition';
  import data from '$lib/yougov.json';
  import { COLORS, DEMOS } from '$lib/meta.js';

  // Party, metric and demographic are owned by the page (controls in sidebar).
  let { party = 'Republican', metric = 'fame', demo = 'everyone' } = $props();

  // the chosen demographic's value for a person (falls back to overall).
  // guarded: d3.hierarchy.sum() also calls this on the parent node, which has
  // no `values`, so return 0 there.
  const value = (d) => {
    const v = d.values?.[demo] ?? d.values?.everyone;
    return v ? (v[metric] ?? 0) : 0;
  };
  // label shown in the tooltip when a specific demographic is selected
  let demoLabel = $derived(
    demo === 'everyone' ? '' : (DEMOS.find((x) => x.key === demo)?.label ?? '')
  );

  // ---- responsive: fill the whole stage rectangle --------------------------
  let chartW = $state(0);
  let chartH = $state(0);

  // ---- layout: d3 computes, Svelte renders ---------------------------------
  // Pack just the selected party's people, sized by the selected metric, into
  // the full width × height of the stage (no centred square → no side margins).
  let people = $derived(data.children.find((c) => c.name === party).children);

  // d3.pack: biggest circle in the centre, others radiating out by size — the
  // clean, deterministic layout. Packed by the current metric into the largest
  // square that fits, then centred. Switching metric re-packs; the CSS
  // transform transition glides each face to its new spot.
  let leaves = $derived.by(() => {
    if (chartW <= 0 || chartH <= 0 || people.length === 0) return [];
    const side = Math.min(chartW, chartH);
    const root = d3
      .hierarchy({ children: people })
      .sum((d) => value(d))
      .sort((a, b) => b.value - a.value);
    d3.pack().size([side, side]).padding(2)(root);
    const dx = (chartW - side) / 2;
    const dy = (chartH - side) / 2;
    return root.leaves().map((n) => ({ d: n.data, x: n.x + dx, y: n.y + dy, r: n.r }));
  });

  // ---- hover ---------------------------------------------------------------
  let hovered = $state(null); // slug
  let tooltip = $state(null);
  function enter(node) {
    hovered = node.d.slug;
    // flip below the face when there isn't room above; clamp x so the card
    // never runs off the left/right edge either
    const below = node.y - node.r < 120;
    tooltip = {
      x: Math.max(100, Math.min(chartW - 100, node.x)),
      y: below ? node.y + node.r : node.y - node.r,
      below,
      person: node.d
    };
  }
  function leave() {
    hovered = null;
    tooltip = null;
  }
</script>

<div class="wrap">
  <div class="chart" bind:clientWidth={chartW} bind:clientHeight={chartH}>
    {#if chartW > 0 && chartH > 0}
      <svg width={chartW} height={chartH} viewBox="0 0 {chartW} {chartH}" role="presentation">
        <defs>
          <clipPath id="faceClip" clipPathUnits="objectBoundingBox">
            <circle cx="0.5" cy="0.5" r="0.5" />
          </clipPath>
        </defs>

        <!-- metric toggle re-packs → the CSS transform transition glides each
             face to its new spot; party swap fades the cast in/out -->
        {#each leaves as node (node.d.slug)}
          <g
            class="node"
            class:dim={hovered && hovered !== node.d.slug}
            class:on={hovered === node.d.slug}
            style="transform: translate({node.x}px, {node.y}px)"
            onmouseenter={() => enter(node)}
            onmouseleave={leave}
            in:fade={{ duration: 250 }}
            out:fade={{ duration: 200 }}
            role="presentation"
          >
            <g class="bubble" style="transform: scale({node.r})">
              <circle class="ring" r="1" fill={COLORS[party]} />
              {#if node.d.img}
                <image
                  href={node.d.img}
                  x="-1"
                  y="-1"
                  width="2"
                  height="2"
                  preserveAspectRatio="xMidYMid slice"
                  clip-path="url(#faceClip)"
                />
              {/if}
              <circle class="stroke" r="1" fill="none" stroke={COLORS[party]} />
            </g>
          </g>
        {/each}
      </svg>

      {#if tooltip}
        {@const person = tooltip.person}
        {@const all = person.values?.everyone ?? { fame: 0, popularity: 0 }}
        {@const metricLabel = metric === 'fame' ? 'Known by' : 'Liked by'}
        <div class="tip" class:below={tooltip.below} style="left: {tooltip.x}px; top: {tooltip.y}px">
          <div class="tip-name">{person.name}</div>
          <div class="tip-meta">
            {party}{person.type && person.type !== 'Public Figure' ? ` · ${person.type}` : ''}
          </div>
          <div class="tip-meta">
            #{person.fameRank} most famous{person.popRank ? ` · #${person.popRank} most liked` : ''}
          </div>

          <!-- overall scores -->
          <div class="tip-bars">
            <div class="bar-row">
              <span>Fame</span>
              <div class="track"><div class="fill fame" style="width: {all.fame}%"></div></div>
              <b>{all.fame}{person.rising.fame ? ' ↑' : ''}</b>
            </div>
            <div class="bar-row">
              <span>Liked</span>
              <div class="track"><div class="fill pop" style="width: {all.popularity}%"></div></div>
              <b>{all.popularity}{person.rising.popularity ? ' ↑' : ''}</b>
            </div>
          </div>

          <!-- per-demographic breakdown of the current metric -->
          <div class="tip-section">{metricLabel} group</div>
          <div class="tip-bars">
            {#each DEMOS.filter((d) => d.key !== 'everyone') as d}
              {@const dv = person.values[d.key]?.[metric]}
              <div class="bar-row demo-row" class:hi={demo === d.key}>
                <span>{d.label}</span>
                <div class="track">
                  <div class="fill {metric}" style="width: {dv ?? 0}%"></div>
                </div>
                <b>{dv ?? '–'}</b>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .wrap {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }
  .chart {
    position: relative;
    flex: 1 1 auto;
    min-height: 0;
    width: 100%;
  }
  svg {
    display: block;
    width: 100%;
    height: 100%;
  }

  /* metric toggle re-packs: the position (outer translate) and size (inner
     scale) both transition so each face glides smoothly to its new spot */
  .node {
    transition:
      transform 600ms cubic-bezier(0.4, 0, 0.2, 1),
      opacity 200ms ease;
    cursor: pointer;
  }
  .node.dim {
    opacity: 0.82;
  }
  .bubble {
    transition: transform 600ms cubic-bezier(0.4, 0, 0.2, 1);
  }
  .ring {
    opacity: 0.25;
  }
  .stroke {
    stroke-width: 0.04;
    stroke-opacity: 0.5;
    vector-effect: non-scaling-stroke;
  }
  .node.on .stroke {
    stroke-width: 2.5;
    stroke-opacity: 1;
    vector-effect: non-scaling-stroke;
  }

  /* tooltip card */
  .tip {
    position: absolute;
    transform: translate(-50%, -100%);
    margin-top: -10px;
    width: 232px;
    background: #fff;
    border: 1px solid #e1e5ea;
    border-radius: 10px;
    padding: 0.6rem 0.75rem;
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.15);
    pointer-events: none;
    z-index: 5;
  }
  /* when anchored below a near-the-top face, drop the card under it instead */
  .tip.below {
    transform: translate(-50%, 0);
    margin-top: 10px;
  }
  .tip-name {
    font-weight: 700;
    font-size: 0.9rem;
    line-height: 1.2;
  }
  .tip-meta {
    font-size: 0.72rem;
    color: #99a;
  }
  .tip-meta:last-of-type {
    margin-bottom: 0.45rem;
  }
  .tip-section {
    margin: 0.55rem 0 0.1rem;
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #aab;
  }
  .bar-row {
    display: grid;
    grid-template-columns: 4.6rem 1fr 1.5rem;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    margin-top: 0.18rem;
  }
  .bar-row span {
    color: #667;
    white-space: nowrap;
  }
  .bar-row b {
    text-align: right;
  }
  /* highlight the currently-selected demographic row */
  .demo-row.hi span,
  .demo-row.hi b {
    color: #1f2933;
    font-weight: 700;
  }
  .track {
    height: 6px;
    background: #eef0f3;
    border-radius: 3px;
    overflow: hidden;
  }
  .fill {
    height: 100%;
    border-radius: 3px;
    background: #888;
  }
  .fill.fame {
    background: #cf3b3b;
  }
  .fill.pop,
  .fill.popularity {
    background: #2f9e6a;
  }
</style>
