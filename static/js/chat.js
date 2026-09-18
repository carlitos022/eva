const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const messages = document.getElementById("messages");
const emotion = document.getElementById("emotion");

function addMessage(text, who){
  const el = document.createElement("div");
  el.className = "msg " + who;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if(!text) return;

  addMessage(text, "user");
  input.value = "";
  input.disabled = true;

  try{
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await response.json();
    if(!response.ok) throw new Error(data.error || "Error");

    addMessage(data.message, "eva");
    emotion.textContent = data.emotion;
    window.setEvaExpression(data.expression);
  }catch(err){
    addMessage("No pude procesar el mensaje: " + err.message, "eva");
  }finally{
    input.disabled = false;
    input.focus();
  }
});
