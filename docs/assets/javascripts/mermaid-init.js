/* Render Mermaid diagrams after initial load and Material instant navigation. */
function renderMermaidDiagrams() {
  if (typeof mermaid === "undefined") return;
  const dark = document.body.getAttribute("data-md-color-scheme") === "slate";
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: dark ? "dark" : "default"
  });
  mermaid.run({ querySelector: ".mermaid" });
}

if (typeof document$ !== "undefined") {
  document$.subscribe(renderMermaidDiagrams);
} else {
  window.addEventListener("DOMContentLoaded", renderMermaidDiagrams);
}
