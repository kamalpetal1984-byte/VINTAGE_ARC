document.querySelectorAll(".like").forEach(button => {
  button.addEventListener("click", async () => {
    const id = button.dataset.id;
    button.disabled = true;
    try {
      const response = await fetch(`/like/${id}`, {method:"POST"});
      const data = await response.json();
      if (data.ok) {
        button.querySelector("span").textContent = data.count;
        button.firstChild.textContent = data.liked ? "♥ Like · " : "♡ Like · ";
      }
    } catch (e) { alert("Could not update like. Check your connection."); }
    finally { button.disabled = false; }
  });
});
