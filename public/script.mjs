import libopus from './libopusjs/libopus.wasm.js';
import { Queue } from './queue.js';

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

const audioContext = new AudioContext({
    sampleRate: kSampleRate,
    channelCount: 1,
    echoCancellation: false,
    autoGainControl: true,
    noiseSuppression: true,
});


let socket = new WebSocket(`wss://stream.upstreet.ai/ws/${userId}/${friendId}`);
socket.binaryType = "arraybuffer";

socket.onopen = function (event) {
    console.log("WebSocket connected");
};

const audioQueue = new Queue();
let playBackInProgress = false;

socket.onmessage = function (event) {
    console.log('recieved from socket', event.data);
    const float32Array = new Float32Array(event.data);
    audioQueue.enqueue(float32Array);
    console.log('Enqueued data', audioQueue.size);

    play();
};


function play(sampleRate) {
    console.log('Queue playback began');
    if(playBackInProgress){
        return;
    }
    
    while(!audioQueue.isEmpty()){
        playBackInProgress = true;
        const data =  audioQueue.dequeue();
        const length = data.length;

        console.log('Dequed', data);
        console.log('About to play', data, length, sampleRate);

        var channels = 1
        var sampleRate = sampleRate || kSampleRate
        var frames = length

        var buffer = audioContext.createBuffer(channels, frames, sampleRate)

        console.log('Setting data to buffer');
        // `data` comes from your Websocket, first convert it to Float32Array
        buffer.getChannelData(0).set(data)

        // buffer.getChannelData(0).buffer = data.buffer;

        console.log('source.buffer = buffer');

        var source = audioContext.createBufferSource()
        source.buffer = buffer;

        console.log('Connecting source');
        // Then output to speaker for example
        source.connect(audioContext.destination)

        console.log('Setting loop to false');

        source.loop = false;

        source.start(0);

        console.log('play started');
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

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = async event => {
                console.log(Date.now(), '======> media recorder data available', event);
                return socket.send(event.data);
            };
            mediaRecorder.start(1000);
            window.mediaRecorder = mediaRecorder;
        })
        .catch(error => {
            console.error("Error accessing microphone:", error);
        });
}

document.getElementById('startVoiceChat').onclick = startVoiceChat;
document.getElementById('stopVoiceChat').onclick = stopVoiceChat;

play();