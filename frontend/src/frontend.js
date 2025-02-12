import React, { useState, useEffect } from 'react';

function VoiceApp() {
    const [text, setText] = useState('');
    const [status, setStatus] = useState('Click "Capture Voice" to start.');
    const [aiResponse, setAiResponse] = useState('');
    const [conversation, setConversation] = useState([]);
    const [queryBrief, setQueryBrief] = useState('');
    const [orderDetails, setOrderDetails] = useState({
        items: "No items provided.",
        customerName: "Not provided."
    });


    // Function to capture voice using Web Speech API
    const captureVoice = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            setStatus('Speech recognition not supported in this browser.');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            setStatus('Listening...');
        };

        recognition.onspeechend = () => {
            recognition.stop();
            setStatus('Processing voice input...');
        };

        recognition.onerror = (event) => {
            setStatus(`Error: ${event.error}`);
            console.error('Speech recognition error:', event.error);
        };

        recognition.onresult = (event) => {
            const recognizedText = event.results[0][0].transcript;
            setText(recognizedText);
            setStatus('Voice recognized. Sending text to AI...');
        };

        recognition.start();
    };

   // Function to send recognized text to backend for AI response
const getAIResponse = async () => {
    if (text) {
        try {
            const response = await fetch('http://10.55.15.205:8080/generate_response_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await response.json();

            if (data.response_text) {
                // Extract the text after "Answer:" for display and TTS
                const answerIndex = data.response_text.indexOf("Answer:");
                let voiceText = data.response_text;

                if (answerIndex !== -1) {
                    voiceText = data.response_text.slice(answerIndex + 7).trim();
                }

                // Set the parsed response text for display and conversation history
                setAiResponse(voiceText);
                setConversation(prev => [...prev, { user: text, ai: voiceText }]);
                setQueryBrief(data.query_brief || '');
            // Convert the extracted response text to speech
            const utterance = new SpeechSynthesisUtterance(voiceText);

         
           

            // Select a specific voice (optional)
            const voices = window.speechSynthesis.getVoices();
            utterance.voice = voices.find(voice => voice.name === 'Google US English'); // Replace with a desired voice

            // Speak the utterance
            window.speechSynthesis.speak(utterance);

            setStatus('AI response spoken.');

            } else {
                setStatus('AI response error.');
                console.error('Error:', data.error);
            }
        } catch (error) {
            setStatus('Error generating response.');
            console.error('Error:', error);
        }
    } else {
        setStatus('No text to send to AI.');
    }
};



    // Automatically trigger `getAIResponse` when `text` is updated
    useEffect(() => {
        if (text) {
            getAIResponse();
        }
    }, [text]);

    const saveConversation = async () => {
        const conversationText = conversation.map(entry => `User: ${entry.user}\nAI: ${entry.ai}`).join('\n\n');
    
        try {
            const response = await fetch('http://10.55.15.205:8080/generate_summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: conversationText })
            });
    
            if (response.ok) {
                const data = await response.json();
                console.log('Backend Response:', data); // Debug backend response
    
                // Update order details state
                const orderDetails = {
                    items: typeof data.Order === 'object' && data.Order !== null ? data.Order : {}, // Safely handle invalid structures
                    customerName: data.Customer || "Not provided."
                };
                setOrderDetails(orderDetails);
                console.log('Order Details:', orderDetails); // Debug log
            } else {
                console.error('Failed to generate conversation summary:', response.statusText);
            }
        } catch (error) {
            console.error('Error generating conversation summary:', error);
        }
    
        // Save the conversation as a file locally
        // const blob = new Blob([conversationText], { type: 'text/plain' });
        // const link = document.createElement('a');
        // link.href = URL.createObjectURL(blob);
        // link.download = 'conversation.txt';
        // link.click();
    
        // Clear the conversation array for the next session
        setConversation([]);
    };
    
    return (
        <div style={{
            textAlign: 'center',
            marginTop: '50px',
            padding: '20px',
            backgroundImage: 'url("/background.jpg")',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            height: '100vh'
        }}>
            <h2 style={{ color: 'white' }}>Voice Recognition and AI Voice Playback</h2>
            <p style={{ color: 'white' }}>{status}</p>
            <input
                type="text"
                value={text}
                readOnly
                style={{
                    width: '300px',
                    padding: '10px',
                    fontSize: '16px',
                    color: 'black',
                    backgroundColor: 'white'
                }}
            />
            <p style={{ color: 'white' }}><strong>AI Response:</strong> {aiResponse}</p>
            <div style={{ marginTop: '20px' }}>
                <button onClick={captureVoice} style={{ padding: '10px 20px', marginRight: '10px' }}>
                    Capture Voice
                </button>
                <button onClick={saveConversation} style={{ padding: '10px 20px' }}>
                    End Conversation
                </button>
            </div>
            <p style={{ marginTop: '20px', color: 'white', fontStyle: 'italic' }}>
                <strong>Query Brief:</strong> {queryBrief || "Waiting for query type..."}
            </p>
        
            <div style={{
    marginTop: '20px',
    padding: '15px',
    width: '400px',
    marginLeft: 'auto',
    marginRight: 'auto',
    backgroundColor: 'white',
    border: '1px solid black',
    borderRadius: '10px'
}}>
    <h3>Order Details</h3>
    <p><strong>Customer Name:</strong> {orderDetails.customerName || "Customer name not provided."}</p>
    <div>
        <strong>Items:</strong>
        {typeof orderDetails.items === 'object' && Object.keys(orderDetails.items).length > 0 ? (
            <ul>
                {Object.entries(orderDetails.items).map(([key, value]) => (
                    <li key={key} style={{ marginBottom: '10px' }}>
                        <strong>{key}:</strong>
                        <div>
                            <p><strong>Quantity:</strong> {value.quantity}</p>
                            <p><strong>Price Per Item:</strong> ${value.price}</p>
                            <p><strong>Description:</strong> {value.description}</p>
                            <p><strong>Total Price:</strong> ${value.total_price}</p>
                        </div>
                    </li>
                ))}
            </ul>
        ) : (
            <p>No items available.</p>
        )}
    </div>
</div>

 </div>
 );
}

export default VoiceApp;