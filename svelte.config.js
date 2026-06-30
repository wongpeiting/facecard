import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		// Fully static output for GitHub Pages.
		adapter: adapter({ fallback: '404.html' }),
		// On Pages the site is served from /<repo>; the CI build sets BASE_PATH.
		// Locally BASE_PATH is unset, so dev/preview run at the root.
		paths: {
			base: process.env.BASE_PATH ?? ''
		}
	}
};

export default config;
