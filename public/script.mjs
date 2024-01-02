import libopus from './libopusjs/libopus.wasm.js';

const queryParams = new URLSearchParams(window.location.search);
if (!queryParams || queryParams.size < 2) {
    alert('Please navigate to https://stream.upstreet.ai/?userId=3000&friendId=200')
}

const userId = queryParams.get('userId');
const friendId = queryParams.get('friendId');
const kSampleRate = 44100;
const bitrate = 60000;
const frameSize = 20;
const voiceOptimization = true;
let audioStream;
let processor;
let audioContext;

let audioContextPlay = new AudioContext();
let source = null;
let audioBufferQueue = [];

let socket;

function registerSocket(model = 'model'){

    socket = new WebSocket(`wss://stream.upstreet.ai/ws/${userId}/${friendId}/${model}`);
    socket.binaryType = "arraybuffer";

    socket.onopen = function (event) {
        console.log("WebSocket connected");
    };

    socket.onmessage = function (event) {
        // console.log('recieved from socket', event.data);
        const float32Array = new Float32Array(event.data);
        var channels = 1
        var sampleRate = sampleRate || kSampleRate
        var frames = float32Array.length

        var buffer = audioContextPlay.createBuffer(channels, frames, sampleRate)

        console.log('Setting data to buffer');
        // `data` comes from your Websocket, first convert it to Float32Array
        buffer.getChannelData(0).set(float32Array)
        // audioQueue.enqueue(float32Array);
        // console.log('Enqueued data', audioQueue.size);
        console.log(buffer)
        //handleIncomingPCMData(event.data);
        audioBufferQueue.push(buffer);
        if (!source) {
            playBufferedAudio();
        }
        //play();
    };

}

// Function to play buffered audio
function playBufferedAudio() {
    if (audioBufferQueue.length > 0) {
        source = audioContextPlay.createBufferSource();
        source.buffer = audioBufferQueue.shift();
        source.connect(audioContextPlay.destination);
        source.onended = playBufferedAudio;
        source.start();
    } else {
        source = null;
    }
}

function stopVoiceChat(userId) {
    if (window.mediaRecorder) {
        window.mediaRecorder.stop();
        window.mediaRecorder = null;
    }

    if(window.microphone){
        window.microphone.disconnect()
    }

    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
    }

    if (processor) {
        processor.disconnect();
        processor = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
}

const encoderPromise = async (channelCount, sampleRate, bitrate, frameSize, voiceOptimization) => {
    await libopus.waitForReady();
    const enc = new libopus.Encoder(channelCount, sampleRate, bitrate, frameSize, voiceOptimization);
    return enc;
}

async function startVoiceChat(userId) {
    if (window.mediaRecorder) {
        return;
    }
    const enc = await encoderPromise(1, kSampleRate, bitrate, frameSize, voiceOptimization);
    let firstChunk = null;

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            processStream(stream);
        })
        .catch(error => {
            console.error("Error accessing microphone:", error);
        });
}

async function processStream(stream) {
    audioStream = stream;
    audioContext = new AudioContext();

    // Load the worklet processor
    await audioContext.audioWorklet.addModule('processor.js');

    const source = audioContext.createMediaStreamSource(stream);
    processor = new AudioWorkletNode(audioContext, 'custom-audio-processor');

    source.connect(processor)

    processor.port.onmessage = event => {
        // Handle messages from the audio processor here
        socket.send(event.data);
    };

    // You can send messages to the audio processor like this
    // processor.port.postMessage({ command: 'start' });
}

document.getElementById('startVoiceChat').onclick = startVoiceChat;
document.getElementById('stopVoiceChat').onclick = stopVoiceChat;

setTimeout(()=>{
    document.getElementById('modelSelect').addEventListener('change', function() {
        var selectedOption = this.options[this.selectedIndex];
        const model = selectedOption.value;
        socket.close();
        socket = null;
        registerSocket(model);
    });
}, 500)


document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    var fileInput = document.getElementById('fileInput').files[0];
    var fileName = document.getElementById('fileName').value;

    if(!fileInput || !fileName){
        alert('Missing Inputs');
        return;
    }    

    var formData = new FormData();

    formData.append('file', fileInput); // Append the file
    formData.append('name', fileName); // Append the file

    fetch(`/add-model/${fileName}`, { // Replace '/upload' with your actual upload URL
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        alert('Upload successful!');
        window.location.reload();
    })
    .catch(error => {
        alert('Something went wrong')
        console.error('Error:', error);
    });
});


registerSocket();