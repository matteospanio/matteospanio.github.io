import { visit } from 'unist-util-visit';

const KINDS = new Set(['note', 'tip', 'warning', 'danger', 'aside']);

/**
 * Turns `:::note{title="…"}` container directives into semantic callouts.
 *
 * Unknown directive names are left alone rather than swallowed, so a typo shows
 * up as visible text instead of silently disappearing from the post.
 */
export function remarkCallout() {
  return (tree) => {
    visit(tree, (node) => {
      if (node.type !== 'containerDirective') return;
      if (!KINDS.has(node.name)) return;

      const title = node.attributes?.title ?? node.name;

      node.data ??= {};
      node.data.hName = 'aside';
      node.data.hProperties = {
        class: `callout callout--${node.name}`,
        role: node.name === 'warning' || node.name === 'danger' ? 'alert' : 'note',
      };

      node.children.unshift({
        type: 'paragraph',
        data: { hName: 'p', hProperties: { class: 'callout__title' } },
        children: [{ type: 'text', value: title }],
      });
    });
  };
}
