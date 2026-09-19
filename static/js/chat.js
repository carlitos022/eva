const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const sendButton = form.querySelector("button");
const messages = document.getElementById("messages");
const emotion = document.getElementById("emotion");
const thinking = document.getElementById("thinking");
const welcomeMessage = document.getElementById("welcomeMessage");

let thinkingTimer = null;
let thinkingShownAt = 0;
let interactionStartedAt = 0;

const MIN_LISTEN_MS = 500;
const MIN_THINK_MS = 450;

function delay(ms){
  return new Promise(resolve => setTimeout(resolve, ms));
}

function addMessage(text, who){
  const el = document.createElement("div");
  el.className = "msg " + who;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

function mapExpression(expression, emotionName){
  const valid = new Set([
    "neutral",
    "happy",
    "curious",
    "concerned",
    "surprised",
    "sad"
  ]);

  if(valid.has(expression)) return expression;

  const fallback = {
    feliz: "happy",
    curiosa: "curious",
    preocupada: "concerned",
    sorprendida: "surprised",
    triste: "sad",
    neutral: "neutral"
  };

  return fallback[emotionName] || "neutral";
}

function stopWaitingAnimations(){
  if(thinkingTimer){
    clearTimeout(thinkingTimer);
    thinkingTimer = null;
  }

  window.setEvaListening(false);
  window.setEvaThinking(false);
  thinking.classList.add("hidden");
}

async function restoreVisualState(){
  try{
    const response = await fetch("/api/state");
    if(!response.ok) return;

    const state = await response.json();
    const expression = mapExpression(null, state.emotion);

    emotion.textContent = state.emotion || "neutral";
    window.setEvaExpression(expression, state.intensity);

    if(Array.isArray(state.memory) && state.memory.length > 0){
      welcomeMessage.textContent = "Hola de nuevo. Estoy lista para continuar nuestra conversacion.";
    }
  }catch(_err){
    // La interfaz puede seguir funcionando aunque el estado inicial no cargue.
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = input.value.trim();
  if(!text) return;

  interactionStartedAt = performance.now();
  thinkingShownAt = 0;

  addMessage(text, "user");
  input.value = "";
  input.disabled = true;
  sendButton.disabled = true;

  window.setEvaListening(true);

  thinkingTimer = setTimeout(() => {
    window.setEvaListening(false);
    window.setEvaThinking(true);
    thinking.classList.remove("hidden");
    thinkingShownAt = performance.now();
    thinkingTimer = null;
  }, MIN_LISTEN_MS);

  try{
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });

    const data = await response.json();

    if(!response.ok){
      throw new Error(data.error || "Error");
    }

    const elapsed = performance.now() - interactionStartedAt;

    if(elapsed < MIN_LISTEN_MS){
      await delay(MIN_LISTEN_MS - elapsed);
    }

    if(thinkingShownAt){
      const thinkingElapsed = performance.now() - thinkingShownAt;
      if(thinkingElapsed < MIN_THINK_MS){
        await delay(MIN_THINK_MS - thinkingElapsed);
      }
    }

    stopWaitingAnimations();

    addMessage(data.message, "eva");

    const emotionName = data.emotion || "neutral";
    const expression = mapExpression(data.expression, emotionName);
    const intensity = Number(data.intensity ?? 0.55);

    emotion.textContent = emotionName;
    window.reactToReply(expression, intensity, data.message.length);
  }catch(err){
    stopWaitingAnimations();
    window.setEvaExpression("concerned", 0.75);
    addMessage("No pude procesar el mensaje: " + err.message, "eva");
  }finally{
    input.disabled = false;
    sendButton.disabled = false;
    input.focus();
  }
});

input.addEventListener("focus", () => {
  if(!input.disabled){
    window.setEvaListening(true);
  }
});

input.addEventListener("blur", () => {
  if(!input.disabled){
    window.setEvaListening(false);
  }
});

restoreVisualState();
