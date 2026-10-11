window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

// Wait for startup and serialize page changes so typesetting cannot overlap.
let mathJaxTypesetting = Promise.resolve();

document$.subscribe(() => {
  mathJaxTypesetting = mathJaxTypesetting.then(async () => {
    const mathJax = window.MathJax;
    // MathJax will typeset the current document itself during initial startup.
    if (!mathJax.startup?.promise) return;

    await mathJax.startup.promise;
    mathJax.startup.output.clearCache();
    mathJax.typesetClear();
    mathJax.texReset();
    await mathJax.typesetPromise();
  }).catch((error) => {
    console.error("MathJax typesetting failed:", error);
  });
});
