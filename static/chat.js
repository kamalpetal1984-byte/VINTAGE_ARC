const log = document.getElementById("chatlog");
if (log) {
  const other = log.dataset.other;
  const myId = Number(log.dataset.me);
  let lastSignature = "";
  async function refresh() {
    try {
      const r = await fetch(`/api/messages/${other}`);
      const data = await r.json();
      const signature = data.messages.map(m => m.id).join(",");
      if (signature === lastSignature) return;
      lastSignature = signature;
      log.replaceChildren();
      data.messages.forEach(m => {
        const item = document.createElement("div");
        item.className = "bubble " + (m.sender_id === myId ? "mine" : "theirs");
        const who = document.createElement("b"); who.textContent = m.sender + " ";
        const body = document.createElement("span"); body.textContent = m.body;
        const time = document.createElement("small"); time.textContent = m.time;
        item.append(who, body, time); log.append(item);
      });
      log.scrollTop = log.scrollHeight;
    } catch(e) {}
  }
  const form = document.getElementById("send-form");
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const input = document.getElementById("message-input");
    const body = input.value.trim();
    if (!body) return;
    const r = await fetch(`/api/messages/${other}`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({body})});
    if (r.ok) { input.value = ""; await refresh(); }
    else alert("Message could not be sent.");
  });
  refresh(); setInterval(refresh, 3000);
}
