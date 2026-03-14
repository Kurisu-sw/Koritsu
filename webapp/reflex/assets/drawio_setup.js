// draw.io postMessage bridge
window.__drawioReady = false;
window.__pendingXml = null;

window.loadDrawioXml = function (xml) {
  var iframe = document.getElementById("drawio-frame");
  if (!iframe || !iframe.contentWindow) return;
  if (window.__drawioReady) {
    iframe.contentWindow.postMessage(
      JSON.stringify({ action: "load", xml: xml }),
      "*"
    );
  } else {
    window.__pendingXml = xml;
  }
};

window.addEventListener("message", function (evt) {
  if (!evt.data || typeof evt.data !== "string") return;
  try {
    var msg = JSON.parse(evt.data);
    if (msg.event === "init") {
      window.__drawioReady = true;
      if (window.__pendingXml) {
        window.loadDrawioXml(window.__pendingXml);
        window.__pendingXml = null;
      }
    }
  } catch (e) {}
});
