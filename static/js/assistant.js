const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");

function appendMessage(text, role='assistant', small=''){
  const el = document.createElement('div');
  el.className = 'bubble ' + (role === 'user' ? 'user' : 'assistant');
  el.innerText = text;
  chat.appendChild(el);
  if(small){
    const s = document.createElement('div');
    s.className = 'small';
    s.innerText = small;
    chat.appendChild(s);
  }
  chat.scrollTop = chat.scrollHeight;
}

//
// ----------- CSRF TOKEN FOR DJANGO -------------
//
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    let cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie("csrftoken");


//
// ----------- CALL DJANGO BACKEND -------------
//
async function askServer(question){
  try{
    const res = await fetch("/assistant/ask/", {
      method: "POST",
      headers: { 
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrftoken
      },
      body: new URLSearchParams({ message: question })
    });

    if(!res.ok){
      appendMessage("Error: " + res.statusText);
      return;
    }

    const json = await res.json();
    appendMessage(
      json.reply || "No answer received",
      "assistant"
    );

  } catch(err){
    appendMessage("Network error — could not reach Django backend.", "assistant");
    console.error(err);
  }
}


//
// ----------- FORM HANDLING -------------
//
form.addEventListener('submit', (e)=>{
  e.preventDefault();
  const text = input.value.trim();
  if(!text) return;
  appendMessage(text, 'user');
  appendMessage('Thinking…', 'assistant');
  askServer(text);
  input.value = '';
});

// Starter message
appendMessage(
  'Hi! Ask me about recipes, ingredients, substitutions, or cooking methods.',
  'assistant'
);
