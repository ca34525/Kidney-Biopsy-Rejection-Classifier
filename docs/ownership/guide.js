"use strict";
const guide = document.querySelector("main");
const functions = [...document.querySelectorAll("details.function")];
const navigation = [...document.querySelectorAll(".sidebar nav a")];
const searchInput = document.getElementById("guide-search");
const searchResults = document.getElementById("search-results");
const searchStatus = document.getElementById("search-status");

function revealTarget() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  const target = document.getElementById(id);
  if (!target) return;
  let parent = target;
  while (parent && parent !== guide) {
    if (parent.tagName === "DETAILS") parent.open = true;
    parent = parent.parentElement;
  }
  requestAnimationFrame(() => target.scrollIntoView({block: "start"}));
}
window.addEventListener("hashchange", revealTarget);
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href^='#']");
  if (link && link.getAttribute("href") === location.hash) revealTarget();
});
document.getElementById("expand-all").addEventListener("click", () => {
  functions.forEach((item) => { item.open = true; });
});
document.getElementById("collapse-all").addEventListener("click", () => {
  functions.forEach((item) => { item.open = false; });
});
document.querySelectorAll("[data-expand-section]").forEach((button) => {
  button.addEventListener("click", () => {
    const cards = [...document.getElementById(button.dataset.expandSection).querySelectorAll("details.function")];
    const shouldOpen = cards.some((card) => !card.open);
    cards.forEach((card) => { card.open = shouldOpen; });
    button.textContent = shouldOpen ? "Collapse functions" : "Expand functions";
  });
});
const searchable = [...document.querySelectorAll("[data-search-title]")].map((element) => ({
  id: element.id,
  title: element.dataset.searchTitle,
  label: element.dataset.searchLabel || "",
  text: (element.dataset.searchTitle + " " + element.textContent).toLowerCase(),
}));
searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim().toLowerCase();
  searchResults.replaceChildren();
  searchStatus.textContent = "";
  if (!query) return;
  const words = query.split(/\s+/);
  const matches = searchable.filter((entry) => words.every((word) => entry.text.includes(word)));
  searchStatus.textContent = `${matches.length} matching explanations`;
  matches.slice(0, 18).forEach((entry) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${entry.id}`;
    link.textContent = entry.title;
    const label = document.createElement("small");
    label.textContent = entry.label;
    link.append(label);
    item.append(link);
    searchResults.append(item);
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.activeElement === searchInput) {
    searchInput.value = "";
    searchInput.dispatchEvent(new Event("input"));
  }
});
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      navigation.forEach((link) => {
        const active = link.hash === `#${entry.target.id}`;
        link.classList.toggle("active", active);
        if (active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    });
  }, {rootMargin: "-5% 0px -75% 0px", threshold: 0});
  document.querySelectorAll("main > header, main > section").forEach((section) => observer.observe(section));
}
let beforePrintState = [];
window.addEventListener("beforeprint", () => {
  beforePrintState = [...document.querySelectorAll("details:not(.source-snippet):not(.source-file)")].map((element) => [element, element.open]);
  beforePrintState.forEach(([element]) => { element.open = true; });
});
window.addEventListener("afterprint", () => beforePrintState.forEach(([element, open]) => { element.open = open; }));
document.getElementById("print-guide").addEventListener("click", () => window.print());
if (location.hash) revealTarget();

const contents = document.getElementById("contents");
const narrowScreen = window.matchMedia("(max-width: 760px)");
function setContentsLayout() { contents.open = !narrowScreen.matches; }
setContentsLayout();
narrowScreen.addEventListener("change", setContentsLayout);
