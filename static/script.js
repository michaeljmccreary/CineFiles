// Codeblock for the Carosel button functionality
const carosel = document.getElementById("Carosel");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
let scrollAmount = 0;
const scrollPerClick = 300;
// Event listeners for the next button
nextBtn.addEventListener("click", () => {
  carosel.scrollBy({ left: scrollPerClick, behavior: "smooth" });
  scrollAmount += scrollPerClick;
});
// Event listener for the previous button - same code as above copied and pased and modified the btn name
prevBtn.addEventListener("click", () => {
  carosel.scrollBy({ left: -scrollPerClick, behavior: "smooth" });
  scrollAmount -= scrollPerClick;
});
