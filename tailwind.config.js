const colors = ['slate', 'gray', 'zinc', 'neutral', 'stone', 'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose'];
const shades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900'];

const safelist = [];
for (const color of colors) {
  for (const shade of shades) {
    safelist.push(`bg-${color}-${shade}`);
    safelist.push(`text-${color}-${shade}`);
    safelist.push(`border-${color}-${shade}`);
    safelist.push(`ring-${color}-${shade}`);
    safelist.push(`hover:bg-${color}-${shade}`);
    safelist.push(`hover:text-${color}-${shade}`);
    safelist.push(`focus:ring-${color}-${shade}`);
    safelist.push(`focus:border-${color}-${shade}`);
  }
}

module.exports = {
  content: ["./templates/**/*.html"],
  safelist: safelist,
  theme: {
    extend: {},
  },
  plugins: [],
}
