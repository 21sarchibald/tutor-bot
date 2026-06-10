const sideBtn = document.querySelector("#sidebarBtn");
const sideBar = document.querySelector("#sidebar");
const chatRoom = document.querySelector("#chatRoom");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");

sideBtn.addEventListener("click", () => {
   sideBar.hidden = !sideBar.hidden;
});
submitBtn.addEventListener("click",()=>{
   let cleanedInput = userPrompt.value.trim();
   if (cleanedInput != ""){
      chatRoom.innerHTML += `
      <p class="userPromptDisplay">${userPrompt.value}</p>`;
      userPrompt.value = "";
   }
});

userPrompt.addEventListener("keypress", (e) => {
   if (e.key === "Enter") {
      submitBtn.click();
   }
});