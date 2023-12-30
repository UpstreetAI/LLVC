import libopus from './libopusjs/libopus.wasm.js';

const queryParams = new URLSearchParams(window.location.search);
if (!queryParams || queryParams.size < 2) {
    alert('Please navigate to http://{HOST}/?userId=3000&friendId=200')
}

const userId = queryParams.get('userId');
const friendId = queryParams.get('friendId');

let socket = new WebSocket(`ws://localhost:8000/ws/${userId}/${friendId}`);

socket.onopen = function (event) {
    console.log("WebSocket connected");
};

socket.onmessage = function (event) {
    document.getElementById("chatlog").value += event.data + "\n";
};

function stopVoiceChat(userId) {
    if (window.mediaRecorder) {
        window.mediaRecorder.stop();
        window.mediaRecorder = null;
    }
}

function startVoiceChat(userId) {
    if (window.mediaRecorder) {
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = async event => {

                console.log(Date.now(), '======> media recorder data available');


                if (event.data.size > 0) {
                    let reader = new FileReader();
                    // reader.onload = function () {
                    //     socket.send(JSON.stringify({
                    //         friendId,
                    //         voice: reader.result
                    //     }));
                    // };
                    // reader.readAsText(event.data);
                    var enc = new TextDecoder("utf-8");

                    socket.send(await event.data.arrayBuffer());

                }
            };
            mediaRecorder.start(1000);
            window.mediaRecorder = mediaRecorder;
        })
        .catch(error => {
            console.error("Error accessing microphone:", error);
        });
}
