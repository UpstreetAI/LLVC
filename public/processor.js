class CustomAudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.sampleRate = sampleRate; // The sample rate of the audio context
        this.chunkSize = this.sampleRate * 1; // Number of samples in 1 second
        this.audioBuffer = new Float32Array(this.chunkSize);
        this.currentPosition = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input.length > 0) {
            const inputChannel = input[0];

            for (let i = 0; i < inputChannel.length; i++) {
                this.audioBuffer[this.currentPosition] = inputChannel[i];
                this.currentPosition++;

                if (this.currentPosition >= this.chunkSize) {
                    // Send the accumulated 1-second audio buffer
                    this.port.postMessage(this.audioBuffer.slice(0));

                    // Reset for the next chunk
                    this.audioBuffer = new Float32Array(this.chunkSize);
                    this.currentPosition = 0;
                }
            }
        }

        return true; // Keep processor alive
    }
}

registerProcessor('custom-audio-processor', CustomAudioProcessor);
