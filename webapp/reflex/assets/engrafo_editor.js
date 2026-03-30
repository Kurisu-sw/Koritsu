/**
 * engrafo_editor.js
 *
 * 1. Resize divider между Tags и Preview панелями.
 * 2. Ctrl+V paste картинок в tag-textarea и expand-textarea.
 */
(function () {
  "use strict";

  var MOBILE_BP = 960;
  var savedRatio = null;

  // ── Resize helpers ──────────────────────────────────────────────────

  function getElements() {
    return {
      layout:  document.querySelector(".engrafo-editor-layout"),
      sidebar: document.querySelector(".engrafo-sidebar"),
      tags:    document.getElementById("engrafo-tags-panel"),
      divider: document.getElementById("engrafo-resize-divider"),
      preview: document.getElementById("engrafo-preview-panel"),
    };
  }

  function clearInlineWidths(els) {
    if (els.tags)    { els.tags.style.flex = ""; els.tags.style.width = ""; }
    if (els.preview) { els.preview.style.flex = ""; els.preview.style.width = ""; }
  }

  function applyRatio() {
    if (savedRatio === null) return;
    if (window.innerWidth <= MOBILE_BP) return;
    var els = getElements();
    if (!els.tags || !els.preview || !els.layout || !els.sidebar) return;
    var gap = 12, divW = els.divider ? els.divider.offsetWidth : 14;
    var avail = els.layout.offsetWidth - els.sidebar.offsetWidth - divW - gap * 3;
    if (avail < 400) { clearInlineWidths(els); savedRatio = null; return; }
    var tagsW = Math.round(avail * savedRatio);
    var prevW = avail - tagsW;
    if (tagsW < 220) { tagsW = 220; prevW = avail - tagsW; }
    if (prevW < 180) { prevW = 180; tagsW = avail - prevW; }
    els.tags.style.flex = "none"; els.tags.style.width = tagsW + "px";
    els.preview.style.flex = "none"; els.preview.style.width = prevW + "px";
  }

  function initResize() {
    var els = getElements();
    if (!els.divider || !els.tags || !els.preview) { setTimeout(initResize, 600); return; }
    els.divider.addEventListener("mousedown", function (e) {
      if (window.innerWidth <= MOBILE_BP) return;
      e.preventDefault();
      var startX = e.clientX, startTagsW = els.tags.offsetWidth, startPrevW = els.preview.offsetWidth;
      var combined = startTagsW + startPrevW;
      document.body.style.userSelect = "none"; document.body.style.cursor = "col-resize";
      function onMove(ev) {
        var dx = ev.clientX - startX;
        var newTagsW = Math.max(220, Math.min(combined - 180, startTagsW + dx));
        els.tags.style.flex = "none"; els.tags.style.width = newTagsW + "px";
        els.preview.style.flex = "none"; els.preview.style.width = (combined - newTagsW) + "px";
        savedRatio = newTagsW / combined;
      }
      function onUp() {
        document.body.style.userSelect = ""; document.body.style.cursor = "";
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }

  var wasMobile = window.innerWidth <= MOBILE_BP;
  window.addEventListener("resize", function () {
    var isMobile = window.innerWidth <= MOBILE_BP;
    if (isMobile) { if (!wasMobile) clearInlineWidths(getElements()); }
    else { applyRatio(); }
    wasMobile = isMobile;
  });

  // ── Image paste (Ctrl+V) ────────────────────────────────────────────

  /**
   * Trigger React's onChange on a textarea via native value setter.
   * Required because React overrides the setter and listens to `input` events.
   */
  function reactSetValue(el, value) {
    var nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, "value"
    ).set;
    nativeSetter.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function initPaste() {
    document.addEventListener("paste", function (e) {
      var focused = document.activeElement;
      if (!focused) return;

      // Find the nearest element with data-tag-key (the tag textarea itself or a parent)
      var tagEl = focused.hasAttribute("data-tag-key")
        ? focused
        : focused.closest("[data-tag-key]");
      if (!tagEl) return;

      var key = tagEl.getAttribute("data-tag-key");
      if (!key) return;

      var items = (e.clipboardData || window.clipboardData || {}).items;
      if (!items) return;

      for (var i = 0; i < items.length; i++) {
        if (items[i].type && items[i].type.startsWith("image/")) {
          e.preventDefault();
          var file = items[i].getAsFile();
          if (!file) continue;
          (function (tagKey) {
            var reader = new FileReader();
            reader.onload = function (ev) {
              var dataUrl = ev.target.result;
              var proxy = document.getElementById("engrafo-paste-proxy");
              if (proxy) {
                reactSetValue(proxy, tagKey + "|||" + dataUrl);
              }
            };
            reader.readAsDataURL(file);
          })(key);
          return;
        }
      }
    }, false);
  }

  // ── Init ───────────────────────────────────────────────────────────

  function init() {
    initResize();
    initPaste();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setTimeout(init, 800); });
  } else {
    setTimeout(init, 800);
  }

  // Re-init on Reflex re-renders (MutationObserver)
  var _resizeInit = false;
  var _pasteInit  = false;
  var domObserver = new MutationObserver(function () {
    if (!_resizeInit && document.getElementById("engrafo-resize-divider")) {
      _resizeInit = true;
      initResize();
    }
    if (!_pasteInit && document.getElementById("engrafo-paste-proxy")) {
      _pasteInit = true;
      initPaste();
    }
  });
  if (document.body) {
    domObserver.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      domObserver.observe(document.body, { childList: true, subtree: true });
    });
  }

})();
