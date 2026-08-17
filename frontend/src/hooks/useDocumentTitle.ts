import { useEffect } from "react";

const BASE = "REC Academic Resource Portal";

/**
 * Sets the browser tab title.
 *
 * The base is department-neutral; the department (and then the page) is
 * appended when one is in context, so the tab reads
 * "REC Academic Resource Portal | Computer Science and Engineering" rather than
 * naming one department for every user of the portal.
 */
export function useDocumentTitle(...parts: (string | null | undefined)[]): void {
  const suffix = parts.filter(Boolean).join(" | ");

  useEffect(() => {
    document.title = suffix ? `${BASE} | ${suffix}` : BASE;
    return () => {
      document.title = BASE;
    };
  }, [suffix]);
}
