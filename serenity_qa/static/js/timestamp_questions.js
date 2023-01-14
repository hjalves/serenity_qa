let player;

const secondsToDuration = (value, hideSeconds) => {
    let secondsValue = Math.floor(value);
    const hours = Math.floor(secondsValue / 3600);
    secondsValue %= 3600;
    const minutes = Math.floor(secondsValue / 60);
    const seconds = secondsValue % 60;
    const formattedHours = String(hours).padStart(2, '0');
    const formattedMinutes = String(minutes).padStart(2, '0');
    const formattedSeconds = String(seconds).padStart(2, '0');
    return hideSeconds
        ? `${formattedHours}:${formattedMinutes}`
        : `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
};

function fillQuestion(target) {
    target.parentElement.classList.add("highlighted");
    const message = target.dataset.message;
    const edit_input = document.getElementById("id_edit_question");
    if (edit_input) {
        edit_input.value += message;
    }
    return false;
}

function seekPlayer(target) {
    console.log(target.dataset);
    if (player) {
        player.seekTo(target.dataset.timestampSec);
        updateLiveStreamChat();
    }
    return false;
}

function getCurrentTime() {
    if (player)
        return player.getCurrentTime();
    return 0;
}

function onPlayerReady(event) {
    console.log("on player ready:", event);
}

function onPlayerStateChange(event) {
    updateLiveStreamChat();
}

function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function updateLiveStreamChat() {
    const currentTime = getCurrentTime();
    document.querySelectorAll('.message').forEach(function (messageEl) {
        const msgTime = parseFloat(messageEl.dataset.timestampSec);
        if (msgTime <= currentTime && messageEl.classList.contains("hidden")) {
            messageEl.classList.remove("hidden");
        } else if (msgTime > currentTime && !messageEl.classList.contains("hidden")) {
            messageEl.classList.add("hidden");
        }
    });
}

function autoUpdateLiveStreamChat() {
    updateLiveStreamChat();
    setTimeout(autoUpdateLiveStreamChat, 5000);
}

function init() {
    autoUpdateLiveStreamChat();
}

document.addEventListener('DOMContentLoaded', init, false);
