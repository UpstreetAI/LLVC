import libopus from './libopusjs/libopus.wasm.js';

const queryParams = new URLSearchParams(window.location.search);
if (!queryParams || queryParams.size < 2) {
    alert('Please navigate to https://stream.upstreet.ai/?userId=3000&friendId=200')
}

const userId = queryParams.get('userId');
const friendId = queryParams.get('friendId');
const kSampleRate = 16000;

let socket = new WebSocket(`wss://stream.upstreet.ai/ws/${userId}/${friendId}`);
socket.binaryType = "arraybuffer";

socket.onopen = function (event) {
    console.log("WebSocket connected");
};

socket.onmessage = function (event) {
    console.log('recieved from socket', event.data);
    const float32Array = new Float32Array(event.data);
    play(float32Array, float32Array.length)
};

function play(data, length, sampleRate) {

    console.log('About to play', data, length, sampleRate);

    var context = new window.AudioContext()

    var channels = 1
    var sampleRate = sampleRate || kSampleRate
    var frames = length

    var buffer = context.createBuffer(channels, frames, sampleRate)

    console.log('Setting data to buffer');
    // `data` comes from your Websocket, first convert it to Float32Array
    buffer.getChannelData(0).set(data)

    // buffer.getChannelData(0).buffer = data.buffer;

    console.log('source.buffer = buffer');

    var source = context.createBufferSource()
    source.buffer = buffer;

    console.log('Connecting source');
    // Then output to speaker for example
    source.connect(context.destination)

    console.log('Setting loop to false');

    source.loop = false;

    source.start(0);

    console.log('play started');
}

function stopVoiceChat(userId) {
    if (window.mediaRecorder) {
        window.mediaRecorder.stop();
        window.mediaRecorder = null;
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
    const enc = await encoderPromise(1, 16000);

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = async event => {

                console.log(Date.now(), '======> media recorder data available');


                if (event.data.size > 0) {
                    let reader = new FileReader();
                    reader.onload = function () {
                        const arrayBuffer = reader.result;
                        console.log('arrayBuffer', arrayBuffer);

                        try {

                            const audioContext = new AudioContext({
                                sampleRate: kSampleRate,
                                channelCount: 1,
                                echoCancellation: false,
                                autoGainControl: true,
                                noiseSuppression: true,
                            });

                            audioContext.decodeAudioData(arrayBuffer, async (audioBuffer) => {
                                // Do something with audioBuffer
                                console.log('audioBuffer', audioBuffer)

                                var offlineContext = new OfflineAudioContext(audioBuffer.numberOfChannels, audioBuffer.length, audioBuffer.sampleRate);
                                var source = offlineContext.createBufferSource();
                                source.buffer = audioBuffer;
                                source.connect(offlineContext.destination);
                                source.start();
                                const renderedBuffer = await offlineContext.startRendering();
                                const audio = renderedBuffer.getChannelData(0);

                                console.log('renderedBuffer', renderedBuffer);

                                //return play(audio, audio.length, renderedBuffer.sampleRate)

                                return socket.send(audio);
                            });
                        } catch (e) {
                            //ignore
                        }


                    };

                    reader.readAsArrayBuffer(event.data);

                    // console.log(enc);
                    // socket.send(floatArray);

                }
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
