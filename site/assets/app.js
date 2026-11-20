(() => {
  "use strict";
  const controls = document.querySelector(".project-controls");
  const search = document.querySelector("#project-search");
  const buttons = [...document.querySelectorAll(".filter-button")];
  const items = [...document.querySelectorAll("#project-list > li")];
  const status = document.querySelector("#result-count");
  const empty = document.querySelector("#empty-state");
  const reset = document.querySelector("#reset-filters");
  const emptyReset = document.querySelector("#empty-reset");
  if (!controls || !search || !status || !empty || !reset || !emptyReset || !items.length) return;
  const normalize = value => value.normalize("NFKC").toLocaleLowerCase("zh-CN").trim();
  const index = items.map(item => ({ item, text: normalize(item.dataset.search || ""), category: item.dataset.category }));
  const categories = new Set(buttons.map(button => button.dataset.category));
  const initial = new URLSearchParams(window.location.search);
  let category = categories.has(initial.get("category")) ? initial.get("category") : "all";
  search.value = (initial.get("q") || "").slice(0, 200);

  function apply(updateUrl = true) {
    const query = normalize(search.value);
    const words = query.split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const entry of index) {
      const matches = (category === "all" || category === entry.category) && words.every(word => entry.text.includes(word));
      entry.item.hidden = !matches;
      if (matches) visible += 1;
    }
    for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset.category === category));
    status.textContent = visible === items.length ? `显示 ${items.length} 个项目` : `显示 ${visible} / ${items.length} 个项目`;
    empty.hidden = visible !== 0;
    reset.hidden = !query && category === "all";
    document.querySelector("#empty-description").textContent = query ? `没有找到与“${search.value.trim()}”匹配的项目。试试其他关键词，或清除筛选。` : "这个分类暂时没有匹配项目，可以查看全部项目。";
    if (updateUrl) {
      const url = new URL(window.location.href);
      if (query) url.searchParams.set("q", search.value.trim()); else url.searchParams.delete("q");
      if (category !== "all") url.searchParams.set("category", category); else url.searchParams.delete("category");
      window.history.replaceState(null, "", url);
    }
  }
  function clear() {
    category = "all";
    search.value = "";
    apply();
    search.focus({ preventScroll: true });
  }
  search.addEventListener("input", () => apply());
  search.addEventListener("keydown", event => {
    if (event.key === "Escape") { event.preventDefault(); clear(); }
  });
  for (const button of buttons) button.addEventListener("click", () => { category = button.dataset.category; apply(); });
  reset.addEventListener("click", clear);
  emptyReset.addEventListener("click", clear);
  document.addEventListener("keydown", event => {
    if (event.key !== "/" || event.ctrlKey || event.altKey || event.metaKey) return;
    const target = event.target;
    if (target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))) return;
    event.preventDefault();
    search.focus();
  });
  apply(false);
  controls.hidden = false;
})();
