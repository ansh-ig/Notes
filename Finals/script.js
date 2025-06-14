// Dynamic Welcome Message
const welcomeMessage = document.getElementById('welcome-message');
const messages = ['Welcome to My Website!!!', 'Explore My Projects!', 'Get to Know Me!'];
let index = 0;

function changeMessage() {
    welcomeMessage.innerText = messages[index];
    index = (index + 1) % messages.length;
}
setInterval(changeMessage, 3000); // Change message every 3 seconds

