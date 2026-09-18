const face = document.getElementById("face");
const pupils = document.querySelectorAll(".pupil");

document.addEventListener("mousemove", (event) => {
  const x = (event.clientX / window.innerWidth - 0.5) * 12;
  const y = (event.clientY / window.innerHeight - 0.5) * 8;
  pupils.forEach((p) => p.style.transform = `translate(${x}px,${y}px)`);
});

function blink(){
  document.querySelectorAll(".eye").forEach(e => e.style.transform += " scaleY(.08)");
  setTimeout(() => {
    document.querySelectorAll(".eye").forEach(e => e.style.transform = "");
  }, 120);
  setTimeout(blink, 2600 + Math.random() * 4200);
}
setTimeout(blink, 1800);

window.setEvaExpression = function(expression){
  face.className = "face " + (expression || "neutral");
};
