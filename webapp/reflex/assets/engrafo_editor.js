/**
 * engrafo_editor.js
 *
 * 1. Resize divider между Tags и Preview панелями.
 * 2. Quill rich-text editors — inline images at cursor, blur sync.
 * 3. Image insertion: Ctrl+V paste (handled by Quill natively) + file picker button.
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

  // ── Trigger React onChange on a hidden textarea ─────────────────────

  function reactSetValue(el, value) {
    var proto = el.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    var nativeSetter = Object.getOwnPropertyDescriptor(proto, "value").set;
    nativeSetter.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // ── Quill helpers ───────────────────────────────────────────────────

  // key → { quill, container, lastFormKey }
  var _quillMap = {};
  // container DOM element → entry (обратная карта для предотвращения дублирования)
  var _containerMap = typeof WeakMap !== "undefined" ? new WeakMap() : null;

  function _containerGet(c) { return _containerMap ? _containerMap.get(c) : c._quillEntry; }
  function _containerSet(c, v) { if (_containerMap) _containerMap.set(c, v); else c._quillEntry = v; }
  function _containerDel(c) { if (_containerMap) _containerMap.delete(c); else delete c._quillEntry; }

  // Простой debounce
  function _debounce(fn, ms) {
    var t;
    return function() { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  function syncQuillToState(key, quill) {
    var proxy = document.getElementById("engrafo-html-proxy");
    if (!proxy) return;
    var html = quill.root.innerHTML || "";
    if (html === "<p><br></p>") html = "";
    reactSetValue(proxy, key + "|||" + html);
  }

  function insertImageIntoQuill(quill, dataUrl) {
    var range = quill.getSelection();
    var index = range ? range.index : quill.getLength();
    quill.insertEmbed(index, "image", dataUrl, Quill.sources.USER);
    quill.setSelection(index + 1, Quill.sources.SILENT);
    // Sync immediately
    var key = quill.container.getAttribute("data-tag-key");
    if (key) syncQuillToState(key, quill);
  }

  function initOneQuill(container) {
    if (typeof Quill === "undefined") return;
    var key = container.getAttribute("data-tag-key");
    if (!key) return;

    var formKey  = container.getAttribute("data-form-key");
    var initHtml = container.getAttribute("data-init-html") || "";

    // ── Проверяем: уже есть Quill на этом контейнере? ──────────────
    var byContainer = _containerGet(container);
    if (byContainer) {
      if (byContainer.key === key) {
        // Тот же тег — обновляем контент если form_key изменился
        if (byContainer.lastFormKey !== formKey) {
          byContainer.lastFormKey = formKey;
          byContainer.quill.root.innerHTML = initHtml;
          byContainer.quill.history.clear();
        }
      } else {
        // Другой тег на том же контейнере (React переиспользовал DOM-элемент)
        // Просто меняем ключ и обновляем контент — не создаём новый Quill
        if (byContainer.key && _quillMap[byContainer.key] === byContainer) {
          delete _quillMap[byContainer.key];
        }
        byContainer.key = key;
        byContainer.lastFormKey = formKey;
        byContainer.quill.root.innerHTML = initHtml;
        byContainer.quill.history.clear();
        _quillMap[key] = byContainer;
        // Обновляем обработчик toolbar (image button берёт key из замыкания)
        var tb = byContainer.quill.getModule("toolbar");
        if (tb) tb.addHandler("image", function () {
          var fi = document.getElementById("engrafo-img-file-input");
          if (!fi) return;
          fi._quillKey = key;
          fi.value = "";
          fi.click();
        });
      }
      return;
    }

    // ── Если по key уже есть запись на другом контейнере — удаляем ─
    var byKey = _quillMap[key];
    if (byKey) {
      _containerDel(byKey.container);
      delete _quillMap[key];
    }

    // ── Создаём новый Quill ─────────────────────────────────────────
    // (используем локальную переменную key чтобы замыкание работало корректно)
    var _key = key;
    var quill = new Quill(container, {
      theme: "snow",
      modules: {
        toolbar: {
          container: [["bold", "italic", "underline"], ["image"], ["clean"]],
          handlers: {
            image: function () {
              var fi = document.getElementById("engrafo-img-file-input");
              if (!fi) return;
              fi._quillKey = _key;
              fi.value = "";
              fi.click();
            }
          }
        },
        clipboard: { matchVisual: false }
      }
    });

    // Устанавливаем начальный HTML
    if (initHtml) quill.root.innerHTML = initHtml;

    var entry = { quill: quill, container: container, key: _key, lastFormKey: formKey };
    _quillMap[_key] = entry;
    _containerSet(container, entry);

    // Sync на blur (selection-change с null range = потеря фокуса).
    // Используем entry.key (не _key!) чтобы всегда брать актуальный ключ
    // даже если контейнер был переиспользован для другого тега.
    quill.on("selection-change", function (range) {
      if (range === null) syncQuillToState(entry.key, quill);
    });

    // Sync с debounce на каждое изменение текста (чтобы State был актуален
    // даже если пользователь кликает "Генерировать" не сделав blur)
    var debouncedSync = _debounce(function () {
      syncQuillToState(entry.key, quill);
    }, 400);
    quill.on("text-change", function (delta, old, source) {
      if (source === Quill.sources.USER) debouncedSync();
    });
  }

  function initQuills() {
    if (typeof Quill === "undefined") return;
    document.querySelectorAll(".tag-quill, .expand-quill").forEach(initOneQuill);
  }

  // ── Image file input (shared, used by toolbar image button) ────────

  var _fileInputInited = false;

  function initFileInput() {
    var fi = document.getElementById("engrafo-img-file-input");
    if (!fi || _fileInputInited) return;
    _fileInputInited = true;

    fi.addEventListener("change", function () {
      var file = fi.files && fi.files[0];
      if (!file) return;
      var key = fi._quillKey || "";
      var entry = _quillMap[key];
      if (!entry) return;
      var reader = new FileReader();
      reader.onload = function (ev) {
        insertImageIntoQuill(entry.quill, ev.target.result);
      };
      reader.readAsDataURL(file);
      fi.value = "";
    });
  }

  // ── img-btn in tag header ─────────────────────────────────────────
  // (kept for backward compat — routes click to the same file input)

  function initImageButtons() {
    document.querySelectorAll(".tag-img-btn[data-img-key]").forEach(function (btn) {
      if (btn._imgInited) return;
      btn._imgInited = true;
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var key = btn.getAttribute("data-img-key");
        var fi = document.getElementById("engrafo-img-file-input");
        if (fi) { fi._quillKey = key; fi.value = ""; fi.click(); }
      });
    });
  }

  // ── Init ───────────────────────────────────────────────────────────

  function init() {
    initResize();
    initFileInput();
    // Quill might not be loaded yet — wait a bit
    if (typeof Quill === "undefined") {
      setTimeout(function () { initQuills(); initImageButtons(); }, 200);
    } else {
      initQuills();
      initImageButtons();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setTimeout(init, 400); });
  } else {
    setTimeout(init, 400);
  }

  // Re-init on Reflex re-renders via MutationObserver
  var _resizeInited = false;
  var _fileInputChecked = false;

  var domObserver = new MutationObserver(function () {
    if (!_resizeInited && document.getElementById("engrafo-resize-divider")) {
      _resizeInited = true;
      initResize();
    }
    if (!_fileInputChecked && document.getElementById("engrafo-img-file-input")) {
      _fileInputChecked = true;
      initFileInput();
    }
    initQuills();
    initImageButtons();
  });

  var _observerOpts = {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-form-key", "data-init-html"],
  };
  if (document.body) {
    domObserver.observe(document.body, _observerOpts);
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      domObserver.observe(document.body, _observerOpts);
    });
  }

})();
