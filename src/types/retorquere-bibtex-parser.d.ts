/**
 * @retorquere/bibtex-parser@10 points `types` at ./dist/types/index.d.ts, but that
 * directory is missing from the published tarball. This declares just the slice of
 * the API this site uses, so the parser stays type-checked rather than `any`.
 */
declare module '@retorquere/bibtex-parser' {
  export interface BibAuthor {
    firstName?: string;
    lastName?: string;
    /** Present when the name could not be split into given/family. */
    name?: string;
  }

  export interface BibEntry {
    key: string;
    type: string;
    /** Verbatim source of this entry, used for the copy-to-clipboard BibTeX block. */
    input?: string;
    fields: Record<string, unknown> & {
      author?: BibAuthor[];
      title?: string;
      year?: string;
    };
  }

  export interface BibFile {
    entries: BibEntry[];
  }

  export interface ParseOptions {
    sentenceCase?: boolean | string[];
    verbatimFields?: (string | RegExp)[];
    [key: string]: unknown;
  }

  export function parse(input: string, options?: ParseOptions): BibFile;
}
