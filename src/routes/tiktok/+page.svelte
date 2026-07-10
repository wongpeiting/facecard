<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import TikTokPack from '$lib/TikTokPack.svelte';
  import { COLORS } from '$lib/meta.js';
  import data from '$lib/tiktok.json';

  const WORLDS = ['Republican', 'Democrat'];
  const ACCOUNTS = { Republican: '@whitehouse and @republicans', Democrat: '@democrats' };
  const EMOTIONS = data.emotions ?? [];
  const HYPE_EMO = ['pride','patriotism','admiration','triumph','inspiration','hope','celebration','confidence','strength','excitement','unity','nostalgia'];

  let world = $state('Republican');
  let emotion = $state(null); // null = size by total posts
  let colorBy = $state('party'); // 'party' | 'lean'

  let userActed = false;
  let timers = [];
  onMount(() => {
    // arrive already on the party the reader was viewing in the fame page
    const w = new URLSearchParams(window.location.search).get('world');
    if (w === 'Democrat' || w === 'Republican') {
      world = w;
      return; // land directly on that party — skip the teaser flip
    }
    timers = [
      setTimeout(() => !userActed && (world = 'Democrat'), 900),
      setTimeout(() => !userActed && (world = 'Republican'), 3400)
    ];
    return () => timers.forEach(clearTimeout);
  });
  function act() {
    if (!userActed) {
      userActed = true;
      timers.forEach(clearTimeout);
    }
  }

  let roster = $derived(data.children.find((c) => c.name === world).children);
  let nFigures = $derived(roster.length);
  let top = $derived(
    emotion
      ? [...roster].filter((p) => p.emotions?.[emotion]).sort((a, b) => b.emotions[emotion] - a.emotions[emotion])[0]
      : roster[0]
  );
  let oppShare = $derived.by(() => {
    const tot = roster.reduce((s, p) => s + p.videos, 0);
    const opp = roster.filter((p) => p.party !== world).reduce((s, p) => s + p.videos, 0);
    return tot ? Math.round((opp / tot) * 100) : 0;
  });

  // ---- timeline scrubber ----
  let MONTHS = $derived(data.children.find((c) => c.name === world).months ?? []);
  let monthIdx = $state(null); // null = all time
  let playing = $state(false);
  let playTimer = null;
  const EVENTS = { '2024-08': 'Harris nominee', '2024-11': 'Election', '2025-01': 'Inauguration' };
  function fmtMonth(m) {
    if (!m) return '';
    const [y, mo] = m.split('-');
    return new Date(+y, +mo - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  }
  function stopPlay() {
    playing = false;
    if (playTimer) clearInterval(playTimer);
    playTimer = null;
  }
  function scrub(e) {
    act();
    stopPlay();
    emotion = null; // month sizing and emotion sizing are mutually exclusive
    monthIdx = +e.target.value;
  }
  function allTime() {
    stopPlay();
    monthIdx = null;
  }
  function togglePlay() {
    act();
    if (playing) return stopPlay();
    emotion = null;
    if (monthIdx === null || monthIdx >= MONTHS.length - 1) monthIdx = 0;
    playing = true;
    playTimer = setInterval(() => {
      if (monthIdx >= MONTHS.length - 1) stopPlay();
      else monthIdx = monthIdx + 1;
    }, 850);
  }
</script>

<main>
  <aside class="sidebar">
    <header>
      <h1 class="headline">
        <span class="switch">
          <span class="sizer" aria-hidden="true">Republican</span>
          {#each WORLDS as w}
            <span class="word" class:active={world === w} style:color={world === w ? COLORS[w] : null}
              role="button" tabindex="0" aria-pressed={world === w}
              onclick={() => { act(); world = w; allTime(); }}
              onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (act(), (world = w), allTime())}>{w}</span>
          {/each}
        </span>
        <span class="anchor">TikTok cast</span>
      </h1>

      <p class="standfirst">
        If political TikTok is a serialized drama, this is the cast list. Here's every face
        <b>{ACCOUNTS[world]}</b> puts on camera <i>or</i> name-drops, sized by how often they appear.
        {#if emotion}
          Cast hardest in
          <b style:color={HYPE_EMO.includes(emotion) ? '#2f9e6a' : '#cf3b3b'}>{emotion}</b>:
          <b>{top?.name}</b>, {top?.emotions[emotion]} posts.
        {/if}
      </p>

      <p class="callout">
        <b>{oppShare}%</b> of this world's attention is on the
        <b style:color={COLORS[world === 'Republican' ? 'Democrat' : 'Republican']}>opposing side</b>.
      </p>

      <div class="controls">
        <div class="ctl">
          <span class="lbl">size by emotion signaled</span>
          <div class="chips">
            <button class:active={emotion === null && monthIdx === null} onclick={() => { act(); emotion = null; allTime(); }}>All posts</button>
            {#each EMOTIONS as e}
              <button class:active={emotion === e} onclick={() => { act(); emotion = e; allTime(); }}>{e}</button>
            {/each}
          </div>
        </div>
        <div class="ctl">
          <span class="lbl">colour the rings by</span>
          <div class="seg">
            <button class:active={colorBy === 'party'} onclick={() => { act(); colorBy = 'party'; }}>Party</button>
            <button class:active={colorBy === 'lean'} onclick={() => { act(); colorBy = 'lean'; }}>Attack ↔ Hype</button>
          </div>
          {#if colorBy === 'party'}
            <div class="clegend">
              <span><i style:background={COLORS.Republican}></i> Republican</span>
              <span><i style:background={COLORS.Democrat}></i> Democrat</span>
            </div>
          {:else}
            <div class="clegend">
              <span style="color:#8e44ad">attacked</span>
              <div class="grad"></div>
              <span style="color:#2f9e6a">celebrated</span>
            </div>
          {/if}
        </div>
      </div>

      <a class="viewswitch" href="{base}/">
        <span class="vs-icon">★</span>
        <b>Who's most popular? →</b>
      </a>
    </header>

    <footer>
      <p class="byline">Built by Wong Pei Ting using D3 on Svelte</p>
    </footer>
  </aside>

  <section class="stage">
    <div class="chartarea">
      <TikTokPack {world} {emotion} {colorBy} {monthIdx} months={MONTHS} />
    </div>
    <div class="timeline">
      <button class="play" onclick={togglePlay} aria-label={playing ? 'pause' : 'play'}>
        {playing ? '⏸' : '▶'}
      </button>
      <div class="tl-track">
        <input
          class="tl-range"
          type="range"
          min="0"
          max={Math.max(0, MONTHS.length - 1)}
          value={monthIdx ?? MONTHS.length - 1}
          oninput={scrub}
          aria-label="timeline month"
        />
        {#each Object.entries(EVENTS) as [m, label]}
          {#if MONTHS.includes(m)}
            <span class="tl-event" style="left: {(MONTHS.indexOf(m) / Math.max(1, MONTHS.length - 1)) * 100}%">
              <i></i><em>{label}</em>
            </span>
          {/if}
        {/each}
      </div>
      <span class="tl-label">{monthIdx === null ? 'All time' : fmtMonth(MONTHS[monthIdx])}</span>
      {#if monthIdx !== null}
        <button class="tl-all" onclick={allTime}>all time</button>
      {/if}
    </div>
  </section>
</main>

<style>
  :global(html, body) { margin: 0; height: 100%; }
  :global(body) { background: #fafafa; color: #1f2933;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
  main { display: flex; height: 100vh; box-sizing: border-box; }
  .sidebar { flex: 0 0 23%; max-width: 23%; display: flex; flex-direction: column;
    justify-content: space-between; padding: 4rem 1.5rem 2rem; box-sizing: border-box;
    border-right: 1px solid #e5e7eb; overflow-y: auto; }
  .stage { flex: 1 1 77%; min-width: 0; padding: 1.5rem 1.75rem; box-sizing: border-box;
    display: flex; flex-direction: column; }
  .chartarea { flex: 1 1 auto; min-height: 0; }
  /* timeline scrubber under the bubbles */
  .timeline { flex: 0 0 auto; display: flex; align-items: center; gap: 0.8rem; padding: 1.4rem 0.5rem 0.3rem; }
  .play { flex: 0 0 auto; width: 34px; height: 34px; border-radius: 50%; border: 0; cursor: pointer;
    background: #1f2933; color: #fff; font-size: 0.8rem; display: grid; place-items: center; }
  .play:hover { background: #333e4c; }
  .tl-track { position: relative; flex: 1 1 auto; }
  .tl-range { width: 100%; margin: 0; accent-color: #1f2933; cursor: pointer; }
  .tl-event { position: absolute; top: 14px; transform: translateX(-50%); white-space: nowrap;
    display: flex; flex-direction: column; align-items: center; pointer-events: none; }
  .tl-event i { width: 1px; height: 8px; background: #b0b6bf; margin-bottom: 2px; }
  .tl-event em { font-style: italic; font-size: 0.64rem; color: #8a94a0; }
  .tl-label { flex: 0 0 auto; font-size: 0.82rem; font-weight: 700; color: #1f2933; min-width: 5.5rem; text-align: right; }
  .tl-all { flex: 0 0 auto; font: inherit; font-size: 0.7rem; padding: 0.15rem 0.5rem; border: 1px solid #d5d9df;
    background: #fff; color: #556; border-radius: 999px; cursor: pointer; }
  .tl-all:hover { border-color: #9aa0a8; }
  .headline { font-size: 2.4rem; font-weight: 800; line-height: 1.04; letter-spacing: -0.025em; margin: 1em 0 0.9rem; }
  .switch { position: relative; display: block; height: 1.08em; }
  .sizer { visibility: hidden; }
  .word { position: absolute; left: 0; top: 0; white-space: nowrap; cursor: pointer; color: #c4c8ce;
    transform: translateY(-1.05em); opacity: 0.4;
    transition: transform 520ms cubic-bezier(0.34,1.25,0.4,1), opacity 400ms ease, color 280ms ease;
    animation: flicker 4.5s ease-in-out 2s infinite; }
  .word:hover { opacity: 0.65; animation: none; }
  .word.active { transform: translateY(0); opacity: 1; cursor: default; animation: none; }
  @keyframes flicker { 0%,88%,100% { opacity: 0.4; } 91% { opacity: 0.72; } 96% { opacity: 0.66; } }
  @media (prefers-reduced-motion: reduce) { .word { animation: none; } }
  .anchor { display: block; }
  .standfirst { font-size: 0.95rem; line-height: 1.5; color: #3a4450; margin: 0 0 1rem; }
  .viewswitch { display: flex; align-items: center; gap: 0.6rem; text-decoration: none; color: #1f2933;
    background: #fff; border: 1px solid #e4e7ec; border-radius: 8px; padding: 0.55rem 0.7rem; margin: 0 0 1rem;
    transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease; }
  .viewswitch:hover { border-color: #b9c0c9; box-shadow: 0 3px 12px rgba(0,0,0,0.07); transform: translateY(-1px); }
  .vs-icon { flex: 0 0 auto; width: 28px; height: 28px; display: grid; place-items: center; border-radius: 50%;
    background: #1f2933; color: #fff; font-size: 0.72rem; }
  .viewswitch b { font-size: 0.86rem; line-height: 1.2; }
  .controls { display: flex; flex-direction: column; gap: 0.7rem; margin-bottom: 0.9rem; }
  .ctl { display: flex; flex-direction: column; gap: 0.35rem; }
  .lbl { font-size: 0.68rem; color: #99a; text-transform: uppercase; letter-spacing: 0.05em; }
  .chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
  .chips button, .seg button {
    font: inherit; font-size: 0.74rem; padding: 0.2rem 0.5rem; border: 1px solid #d5d9df;
    background: #fff; color: #556; border-radius: 999px; cursor: pointer; text-transform: capitalize;
    transition: all 150ms ease; }
  .seg button { border-radius: 6px; }
  .chips button:hover, .seg button:hover { border-color: #9aa0a8; }
  .chips button.active, .seg button.active { background: #1f2933; color: #fff; border-color: #1f2933; }
  .clegend { display: flex; align-items: center; gap: 0.4rem; font-size: 0.7rem; color: #667; margin-top: 0.1rem; }
  .clegend span { display: inline-flex; align-items: center; gap: 0.25rem; white-space: nowrap; }
  .clegend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .clegend .grad { flex: 1; min-width: 34px; height: 6px; border-radius: 3px;
    background: linear-gradient(90deg, #8e44ad, #c9ccd2 50%, #2f9e6a); }
  .callout { font-size: 0.85rem; line-height: 1.5; color: #3a4450; background: #fff; border: 1px solid #ececf0;
    border-left: 3px solid #cbd0d6; border-radius: 6px; padding: 0.55rem 0.7rem; margin: 0 0 1.4rem; }
  footer { font-size: 0.68rem; color: #8a94a0; line-height: 1.4; margin-top: 1rem; }
  .byline { margin-top: 0.5rem; color: #667; }
  footer a { color: inherit; }
  @media (max-width: 760px) {
    main { flex-direction: column-reverse; height: auto; }
    .sidebar, .stage { flex: none; max-width: 100%; width: 100%; }
    .sidebar { padding: 1.5rem 1.25rem; }
    .stage { height: 72vh; }
  }
</style>
