// Shared chart metadata, used by both the page (controls) and the chart.
export const PARTIES = ['Republican', 'Democrat'];

export const METRICS = {
  fame: { label: 'Fame', blurb: '% of Americans who know who they are' },
  popularity: { label: 'Popularity', blurb: '% with a positive opinion of them' }
};

// demographic crossbreaks (in display order). "Everyone" is the default, so it
// sits last — the specific demographics lead.
export const DEMOS = [
  { key: 'women', label: 'Women' },
  { key: 'men', label: 'Men' },
  { key: 'millennials', label: 'Millennials' },
  { key: 'generationx', label: 'Gen X' },
  { key: 'babyboomers', label: 'Boomers' },
  { key: 'everyone', label: 'Everyone' }
];

export const COLORS = { Republican: '#cf3b3b', Democrat: '#2f5e9e' };
