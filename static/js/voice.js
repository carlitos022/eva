const voiceToggle = document.getElementById("voiceToggle");

let evaVoiceEnabled = localStorage.getItem("eva_voice_enabled") !== "false";
let evaVoice = null;

function updateVoiceButton(){
  if(!voiceToggle) return;

  voiceToggle.textContent = evaVoiceEnabled ? "🔊 Voz" : "🔇 Voz";
  voiceToggle.classList.toggle("off", !evaVoiceEnabled);
  voiceToggle.setAttribute(
    "aria-pressed",
    evaVoiceEnabled ? "true" : "false"
  );
}

function chooseVoice(){
  if(!("speechSynthesis" in window)) return;

  const voices = window.speechSynthesis.getVoices();

  if(!voices.length) return;

  const spanish = voices.filter((voice) =>
    (voice.lang || "").toLowerCase().startsWith("es")
  );

  const preferredNames = [
    "helena",
    "elvira",
    "sabina",
    "monica",
    "mónica",
    "paulina",
    "dalia",
    "female"
  ];

  evaVoice =
    spanish.find((voice) =>
      preferredNames.some((name) =>
        voice.name.toLowerCase().includes(name)
      )
    ) ||
    spanish.find((voice) =>
      (voice.lang || "").toLowerCase().startsWith("es-es")
    ) ||
    spanish[0] ||
    voices[0];
}

if("speechSynthesis" in window){
  chooseVoice();
  window.speechSynthesis.onvoiceschanged = chooseVoice;
}

if(voiceToggle){
  voiceToggle.addEventListener("click", () => {
    evaVoiceEnabled = !evaVoiceEnabled;
    localStorage.setItem(
      "eva_voice_enabled",
      evaVoiceEnabled ? "true" : "false"
    );

    if(!evaVoiceEnabled && "speechSynthesis" in window){
      window.speechSynthesis.cancel();
      window.setEvaSpeaking(false);
    }

    updateVoiceButton();
  });
}

window.speakEva = function(text){
  if(
    !evaVoiceEnabled ||
    !("speechSynthesis" in window) ||
    !text
  ){
    return false;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = evaVoice?.lang || "es-ES";
  utterance.rate = 0.98;
  utterance.pitch = 1.06;
  utterance.volume = 1.0;

  if(evaVoice){
    utterance.voice = evaVoice;
  }

  utterance.onstart = () => {
    window.setEvaSpeaking(true, 600000);
  };

  utterance.onend = () => {
    window.setEvaSpeaking(false);
  };

  utterance.onerror = () => {
    window.setEvaSpeaking(false);
  };

  window.speechSynthesis.speak(utterance);
  return true;
};

window.isEvaVoiceEnabled = function(){
  return evaVoiceEnabled;
};

updateVoiceButton();
