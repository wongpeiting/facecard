<script>
  import { onMount } from 'svelte';
  import CirclePack from '$lib/CirclePack.svelte';
  import { PARTIES, METRICS, DEMOS, COLORS } from '$lib/meta.js';
  import data from '$lib/yougov.json';

  let party = $state('Republican');
  let metric = $state('popularity');
  let demo = $state('everyone');

  // On load, flip to Democrat and hold ~2.5s (so the Democrat board is actually readable), then settle back to the Republican default — signalling that the headline is clickable. Cancels the moment the user touches any control.
  let userActed = false;
  let timers = [];
  onMount(() => {
    timers = [
      setTimeout(() => !userActed && (party = 'Democrat'), 800),
      setTimeout(() => !userActed && (party = 'Republican'), 3300)
    ];
    return () => timers.forEach(clearTimeout);
  });
  function act() {
    if (!userActed) {
      userActed = true;
      timers.forEach(clearTimeout);
    }
  }

  // date this data was pulled, formatted e.g. "30 June 2026"
  const asOf = data.updated
    ? new Date(data.updated + 'T00:00:00').toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      })
    : null;
</script>

<main>
  <aside class="sidebar">
    <header>
      <!-- The headline IS the party switch: the picked word drops onto the baseline next to "facecards"; the other lifts up, small and grey. "facecards" never moves because the invisible sizer fixes the width. -->
      <h1 class="headline">
        <span class="switch">
          <span class="sizer" aria-hidden="true">Republican</span>
          {#each PARTIES as p}
            <span
              class="word"
              class:active={party === p}
              style:color={party === p ? COLORS[p] : null}
              role="button"
              tabindex="0"
              aria-pressed={party === p}
              onclick={() => {
                act();
                party = p;
              }}
              onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (act(), (party = p))}
            >
              {p}
            </span>
          {/each}
        </span>
        <span class="anchor">face cards</span>
      </h1>

      <p class="standfirst">
        As the midterms near, both of America's political parties are still searching for someone
        capable of cutting through the noise and commanding attention on demand – or, as Gen Z might
        put it, a face card that never declines. Here's how the hunt for their next main character
        is shaping up.
      </p>

      <div class="controls">
        <div class="seg metric">
          <span class="lbl">size by</span>
          {#each Object.entries(METRICS) as [key, m]}
            <button
              class:active={metric === key}
              onclick={() => {
                act();
                metric = key;
              }}>{m.label}</button
            >
          {/each}
        </div>
        <div class="seg demo">
          <span class="lbl">among</span>
          {#each DEMOS as d}
            <button
              class:active={demo === d.key}
              onclick={() => {
                act();
                demo = d.key;
              }}>{d.label}</button
            >
          {/each}
        </div>
      </div>
    </header>

    <footer>
      <p>
        Source: YouGov Ratings (fame &amp; popularity of US public figures){#if asOf}, as of
          {asOf}{/if}. YouGov surveys daily and refreshes its published ratings quarterly; this
        chart re-pulls the latest automatically each quarter.
      </p>
      <p class="byline">Built by Wong Pei Ting using D3 on Svelte</p>
    </footer>
  </aside>

  <section class="stage">
    <CirclePack {party} {metric} {demo} />
  </section>
</main>

<style>
  :global(html, body) {
    margin: 0;
    height: 100%;
  }
  :global(body) {
    background: #fafafa;
    color: #1f2933;
    font-family:
      -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  }
  main {
    display: flex;
    height: 100vh;
    box-sizing: border-box;
  }
  .sidebar {
    flex: 0 0 20%;
    max-width: 20%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 6rem 1.5rem 2.25rem; /* extra quiet space at the top */
    box-sizing: border-box;
    border-right: 1px solid #e5e7eb;
    overflow-y: auto;
  }
  .stage {
    flex: 1 1 80%;
    min-width: 0;
    padding: 1.5rem 1.75rem;
    box-sizing: border-box;
  }
  /* ---- the toggling headline ---- */
  /* Two lines, left-aligned: the chosen party word on top, "facecards" below it (and fixed). The unchosen word ghosts up into the space above, small and grey; clicking it drops it onto the line. */
  .headline {
    font-size: 2.85rem;
    font-weight: 800;
    line-height: 1.04;
    letter-spacing: -0.025em;
    margin: 1.5em 0 0.9rem; /* top room for the faded word above */
  }
  .switch {
    position: relative;
    display: block;
    height: 1.08em;
  }
  /* invisible: only there to reserve the width of the longest word so the line never reflows when the party changes */
  .sizer {
    visibility: hidden;
  }
  /* non-picked word: same size as the picked one, just sat a line above and faded out. The picked word drops onto the line in party colour. */
  .word {
    position: absolute;
    left: 0;
    top: 0;
    white-space: nowrap;
    cursor: pointer;
    color: #c4c8ce;
    transform: translateY(-1.05em);
    opacity: 0.4;
    transition:
      transform 520ms cubic-bezier(0.34, 1.25, 0.4, 1),
      opacity 400ms ease,
      color 280ms ease;
    /* a faint, periodic flicker to entice clicking the unpicked party */
    animation: flicker 4.5s ease-in-out 2s infinite;
  }
  .word:hover {
    opacity: 0.65;
    animation: none; /* settle + brighten when the reader engages */
  }
  .word.active {
    transform: translateY(0);
    opacity: 1;
    cursor: default;
    animation: none; /* the picked word never flickers */
  }
  @keyframes flicker {
    0%,
    88%,
    100% {
      opacity: 0.4;
    }
    91% {
      opacity: 0.72;
    }
    93% {
      opacity: 0.46;
    }
    96% {
      opacity: 0.66;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .word {
      animation: none;
    }
  }
  .anchor {
    display: block;
  }
  .standfirst {
    font-size: 0.98rem;
    line-height: 1.55;
    color: #3a4450;
    margin: 0 0 1.25rem;
  }

  /* controls — moved here, under the dek */
  .controls {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
  }
  .seg {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    flex-wrap: wrap;
  }
  .lbl {
    font-size: 0.8rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  button {
    border: 1px solid #cbd2d9;
    background: #fff;
    border-radius: 999px;
    padding: 0.32rem 0.9rem;
    font-size: 0.85rem;
    cursor: pointer;
    transition:
      background 150ms,
      color 150ms,
      border-color 150ms;
  }
  button:hover {
    border-color: #888;
  }
  /* both the metric and demographic toggles share the active style */
  .seg button.active {
    background: #1f2933;
    border-color: #1f2933;
    color: #fff;
  }

  footer {
    margin-top: 1.5rem;
    border-top: 1px solid #e5e7eb;
    padding-top: 0.85rem;
  }
  footer p {
    font-size: 0.68rem;
    color: #8a93a0;
    line-height: 1.5;
    margin: 0;
  }
  .byline {
    margin-top: 0.5rem;
    font-weight: 600;
    color: #6b7480;
  }

  /* stack on narrow screens */
  @media (max-width: 760px) {
    main {
      flex-direction: column;
      height: auto;
      min-height: 100vh;
    }
    /* chart first, copy after */
    .stage {
      order: -1;
      flex: 0 0 auto;
      width: 100%;
      height: 82vh;
      padding: 1rem;
    }
    .sidebar {
      order: 0;
      flex: 0 0 auto;
      max-width: none;
      border-right: none;
      border-top: 1px solid #e5e7eb; /* divider now sits above the copy */
      padding: 1.75rem 1.5rem 2.25rem; /* drop the desktop top gap */
    }
  }
</style>
