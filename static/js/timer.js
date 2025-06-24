let totalTime = 25 * 60;
let timer;
function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => {
        if (totalTime <= 0) {
            clearInterval(timer);
            alert("Time's up!");
        } else {
            totalTime--;
            const minutes = Math.floor(totalTime / 60);
            const seconds = totalTime % 60;
            document.getElementById("timer").innerText = 
                `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }, 1000);
}
function resetTimer() {
    clearInterval(timer);
    totalTime = 25 * 60;
    document.getElementById("timer").innerText = "25:00";
}
