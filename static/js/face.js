const head = document.getElementById("head");
const avatar = document.getElementById("avatar");
const mouth = document.getElementById("mouth");
const irises = [...document.querySelectorAll(".iris")];
const upperLids = [...document.querySelectorAll(".lid-upper")];
const lowerLids = [...document.querySelectorAll(".lid-lower")];
const activity = document.getElementById("activity");

const expressions = new Set([
  "neutral",
  "happy",
  "curious",
  "concerned",
  "surprised",
  "sad"
]);

let currentExpression = "neutral";
let currentActivity = "idle";
let speakingInterval = null;
let speakingStopTimer = null;
let microSmileTimer = null;

let targetEyeX = 0;
let targetEyeY = 0;
let eyeX = 0;
let eyeY = 0;

let targetHeadX = 0;
let targetHeadY = 0;
let headX = 0;
let headY = 0;

let lastPointerMove = Date.now();

function clamp(value, min, max){
  return Math.max(min, Math.min(max, value));
}

function setActivityLabel(text){
  if(activity) activity.textContent = text;
}

function applyHeadClasses(){
  head.className = `head ${currentExpression}`;
  if(currentActivity === "thinking") head.classList.add("thinking");
  if(currentActivity === "listening") head.classList.add("listening");
}

function animateFace(){
  eyeX += (targetEyeX - eyeX) * 0.13;
  eyeY += (targetEyeY - eyeY) * 0.13;
  headX += (targetHeadX - headX) * 0.08;
  headY += (targetHeadY - headY) * 0.08;

  irises.forEach((iris) => {
    iris.style.transform = `translate3d(${eyeX}px,${eyeY}px,0)`;
  });

  head.style.transform =
    `rotateX(${headY}deg) rotateY(${headX}deg) translateZ(0)`;

  requestAnimationFrame(animateFace);
}
requestAnimationFrame(animateFace);

document.addEventListener("mousemove", (event) => {
  lastPointerMove = Date.now();

  const nx = event.clientX / window.innerWidth - 0.5;
  const ny = event.clientY / window.innerHeight - 0.5;

  targetEyeX = clamp(nx * 24, -11, 11);
  targetEyeY = clamp(ny * 16, -7, 7);

  targetHeadX = clamp(nx * 7, -3.5, 3.5);
  targetHeadY = clamp(-ny * 5, -2.5, 2.5);
});

function randomIdleGaze(){
  if(Date.now() - lastPointerMove > 3500 && currentActivity !== "speaking"){
    targetEyeX = (Math.random() - 0.5) * 12;
    targetEyeY = (Math.random() - 0.5) * 6;
    targetHeadX = targetEyeX * 0.12;
    targetHeadY = -targetEyeY * 0.12;
  }

  setTimeout(randomIdleGaze, 1800 + Math.random() * 2600);
}
setTimeout(randomIdleGaze, 1800);

function closeEyes(){
  upperLids.forEach((lid) => lid.style.transform = "translateY(0%)");
  lowerLids.forEach((lid) => lid.style.transform = "translateY(0%)");
}

function openEyes(){
  upperLids.forEach((lid) => lid.style.transform = "translateY(-104%)");
  lowerLids.forEach((lid) => lid.style.transform = "translateY(108%)");
}

function singleBlink(duration = 115){
  closeEyes();
  setTimeout(openEyes, duration);
}

function scheduleBlink(){
  const doubleBlink = Math.random() < 0.17;

  singleBlink(105 + Math.random() * 45);

  if(doubleBlink){
    setTimeout(() => singleBlink(95), 220);
  }

  setTimeout(scheduleBlink, 2200 + Math.random() * 4300);
}
setTimeout(scheduleBlink, 1400);

function microSmile(){
  if(currentActivity === "idle" && ["neutral","happy","curious"].includes(currentExpression)){
    head.classList.add("micro-smile");
    setTimeout(() => head.classList.remove("micro-smile"), 700);
  }

  microSmileTimer = setTimeout(microSmile, 7000 + Math.random() * 9000);
}
microSmileTimer = setTimeout(microSmile, 6500);

function clearVisemes(){
  mouth.classList.remove("speaking","viseme-a","viseme-e","viseme-o","viseme-m");
}

function nextViseme(){
  const visemes = ["viseme-a","viseme-e","viseme-o","viseme-m"];
  const next = visemes[Math.floor(Math.random() * visemes.length)];

  mouth.classList.remove(...visemes);
  mouth.classList.add("speaking", next);
}

window.setEvaExpression = function(expression, intensity = 0.55){
  currentExpression = expressions.has(expression) ? expression : "neutral";
  document.documentElement.style.setProperty(
    "--emotion-intensity",
    String(clamp(Number(intensity) || 0.55, 0, 1))
  );
  applyHeadClasses();
};

window.setEvaListening = function(active){
  if(active){
    currentActivity = "listening";
    setActivityLabel("Escuchando");
    targetEyeX = 2;
    targetEyeY = 0;
    targetHeadX = 2.8;
    targetHeadY = 1.4;
  }else if(currentActivity === "listening"){
    currentActivity = "idle";
    setActivityLabel("Lista");
    targetEyeX = 0;
    targetEyeY = 0;
    targetHeadX = 0;
    targetHeadY = 0;
  }
  applyHeadClasses();
};

window.setEvaThinking = function(active){
  if(active){
    currentActivity = "thinking";
    setActivityLabel("Pensando");
    targetEyeX = 5;
    targetEyeY = -5;
    targetHeadX = -3.1;
    targetHeadY = -1.9;
  }else if(currentActivity === "thinking"){
    currentActivity = "idle";
    setActivityLabel("Lista");
    targetEyeX = 0;
    targetEyeY = 0;
    targetHeadX = 0;
    targetHeadY = 0;
  }
  applyHeadClasses();
};

window.setEvaSpeaking = function(active, duration = 1800){
  if(speakingInterval){
    clearInterval(speakingInterval);
    speakingInterval = null;
  }
  if(speakingStopTimer){
    clearTimeout(speakingStopTimer);
    speakingStopTimer = null;
  }

  if(!active){
    clearVisemes();
    if(currentActivity === "speaking"){
      currentActivity = "idle";
      setActivityLabel("Lista");
    }
    applyHeadClasses();
    return;
  }

  currentActivity = "speaking";
  setActivityLabel("Hablando");
  applyHeadClasses();

  nextViseme();
  speakingInterval = setInterval(nextViseme, 145 + Math.random() * 70);

  speakingStopTimer = setTimeout(() => {
    window.setEvaSpeaking(false);
  }, duration);
};

window.reactToReply = function(expression, intensity, textLength){
  window.setEvaExpression(expression, intensity);

  const duration = clamp(850 + (Number(textLength) || 0) * 24, 1200, 4600);
  window.setEvaSpeaking(true, duration);
};

window.addEventListener("beforeunload", () => {
  if(speakingInterval) clearInterval(speakingInterval);
  if(speakingStopTimer) clearTimeout(speakingStopTimer);
  if(microSmileTimer) clearTimeout(microSmileTimer);
});
