/**
 * engrafo_editor.js
 * Resize divider между Tags и Preview панелями.
 *
 * Хранит пропорцию (ratio) вместо пиксельных значений,
 * при ресайзе окна пересчитывает ширины по текущему доступному месту.
 */
(function () {
  "use strict";

  var MOBILE_BP = 960;

  // ratio = доля tags-панели от (tags + preview).  null = не задано (CSS по умолчанию)
  var savedRatio = null;

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
    if (els.tags) {
      els.tags.style.flex  = "";
      els.tags.style.width = "";
    }
    if (els.preview) {
      els.preview.style.flex  = "";
      els.preview.style.width = "";
    }
  }

  /** Применить сохранённый ratio к текущим размерам. */
  function applyRatio() {
    if (savedRatio === null) return;
    if (window.innerWidth <= MOBILE_BP) return;

    var els = getElements();
    if (!els.tags || !els.preview || !els.layout || !els.sidebar) return;

    var gap     = 12;  // CSS gap
    var divW    = els.divider ? els.divider.offsetWidth : 14;
    var sideW   = els.sidebar.offsetWidth;
    var totalW  = els.layout.offsetWidth;
    var avail   = totalW - sideW - divW - gap * 3;  // пространство для tags+preview

    if (avail < 400) {
      // Слишком мало места — сбрасываем на CSS-дефолты
      clearInlineWidths(els);
      savedRatio = null;
      return;
    }

    var tagsW    = Math.round(avail * savedRatio);
    var previewW = avail - tagsW;

    // Кламп минимумов
    var minTags = 220, minPreview = 180;
    if (tagsW < minTags) {
      tagsW = minTags;
      previewW = avail - tagsW;
    }
    if (previewW < minPreview) {
      previewW = minPreview;
      tagsW = avail - previewW;
    }

    els.tags.style.flex    = "none";
    els.tags.style.width   = tagsW + "px";
    els.preview.style.flex  = "none";
    els.preview.style.width = previewW + "px";
  }

  function initResize() {
    var els = getElements();
    if (!els.divider || !els.tags || !els.preview) {
      setTimeout(initResize, 600);
      return;
    }

    els.divider.addEventListener("mousedown", function (e) {
      if (window.innerWidth <= MOBILE_BP) return;
      e.preventDefault();

      var startX        = e.clientX;
      var startTagsW    = els.tags.offsetWidth;
      var startPreviewW = els.preview.offsetWidth;
      var combined      = startTagsW + startPreviewW;

      document.body.style.userSelect = "none";
      document.body.style.cursor     = "col-resize";

      function onMove(ev) {
        var dx       = ev.clientX - startX;
        var newTagsW = Math.max(220, Math.min(combined - 180, startTagsW + dx));
        var newPrevW = combined - newTagsW;

        els.tags.style.flex    = "none";
        els.tags.style.width   = newTagsW + "px";
        els.preview.style.flex  = "none";
        els.preview.style.width = newPrevW + "px";

        // Сохраняем пропорцию
        savedRatio = newTagsW / combined;
      }

      function onUp() {
        document.body.style.userSelect = "";
        document.body.style.cursor     = "";
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup",   onUp);
      }

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup",   onUp);
    });
  }

  // ── Window resize: пересчитать или сбросить ──────────────────────
  var wasMobile = window.innerWidth <= MOBILE_BP;

  window.addEventListener("resize", function () {
    var isMobile = window.innerWidth <= MOBILE_BP;

    if (isMobile) {
      if (!wasMobile) {
        // Только что стали мобильными — убрать inline стили
        clearInlineWidths(getElements());
      }
    } else {
      // Десктоп — пересчитать по ratio
      applyRatio();
    }

    wasMobile = isMobile;
  });

  // ── Init ─────────────────────────────────────────────────────────
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setTimeout(initResize, 800); });
  } else {
    setTimeout(initResize, 800);
  }

  // Re-init on DOM changes (Reflex re-renders)
  var _resizeInit = false;
  var observer = new MutationObserver(function () {
    if (!_resizeInit && document.getElementById("engrafo-resize-divider")) {
      _resizeInit = true;
      initResize();
    }
  });
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }

})();
