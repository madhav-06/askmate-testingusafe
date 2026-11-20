// The chat page: send the question to /api/ask and show the reply. Text is added as text, never as HTML,
// so nothing a customer or the AI types can run as code on this page.
(function () {
  var chat = document.getElementById("chat"), form = document.getElementById("ask"), input = document.getElementById("q");

  function add(text, who) {
    var div = document.createElement("div");
    div.className = "msg " + who;
    div.textContent = text;
    chat.appendChild(div);
    div.scrollIntoView({ block: "end" });
  }

  fetch("/healthz").then(function (r) { return r.json(); }).then(function (h) {
    if (h.name) { document.getElementById("name").textContent = h.name; document.title = h.name; }
    (h.suggestions || []).forEach(function (q) {           // the three questions you chose in askmate.json, as buttons
      var b = document.createElement("button");
      b.type = "button"; b.className = "suggest"; b.textContent = q;
      b.addEventListener("click", function () { input.value = q; form.requestSubmit(); });
      document.getElementById("suggestions").appendChild(b);
    });
  }).catch(function () {});

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    add(q, "me");
    input.value = "";
    fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        add(data.answer || "Sorry, something went wrong.", "bot");
        document.getElementById("resting").hidden = !data.resting;
      })
      .catch(function () { add("The app is waking up. Please try again in a minute.", "bot"); });
  });
})();
