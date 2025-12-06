import { useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { useState } from "react";
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

export const UI = ({ hidden, ...props }) => {

  const input = useRef();
  const [inputText, setInputText] = useState("");
  const [micPermission, setMicPermission] = useState(null);
  const silenceTimerRef = useRef(null);  // ← Timer para detectar silencio

  const { chat, loading, cameraZoomed, setCameraZoomed, message, setAnimationChat } = useChat();
  
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
    isMicrophoneAvailable
  } = useSpeechRecognition();

  // Verificar permisos del micrófono al cargar
  useEffect(() => {
    const checkMicPermission = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('✅ Permiso de micrófono concedido');
        setMicPermission(true);
        stream.getTracks().forEach(track => track.stop());
      } catch (error) {
        console.error('❌ Error de permiso de micrófono:', error);
        setMicPermission(false);
      }
    };

    checkMicPermission();
  }, []);

  // Actualizar el input cuando cambia el transcript
  useEffect(() => {
    console.log('📝 Transcript actualizado:', transcript);
    if (transcript) {
      setInputText(transcript);
      
      // Resetear el timer de silencio cada vez que cambia el transcript
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }

      // Configurar nuevo timer: si no hay cambios en 3 segundos, enviar automáticamente
      silenceTimerRef.current = setTimeout(() => {
        if (transcript.trim() && listening) {
          console.log('⏱️ Silencio detectado - Enviando automáticamente...');
          sendMessageAuto();
        }
      }, 3000); // ← 3 segundos de silencio
    }
  }, [transcript]);

  // Limpiar timer al desmontar
  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, []);

  const handleMicClick = async () => {
    if (listening) {
      console.log('🛑 Deteniendo escucha...');
      
      // Limpiar timer al detener manualmente
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      
      SpeechRecognition.stopListening();
    } else {
      console.log('▶️ Iniciando escucha...');
      
      if (micPermission === false) {
        alert('Debes habilitar el micrófono en la configuración del navegador');
        return;
      }

      resetTranscript();
      setInputText('');
      
      try {
        await SpeechRecognition.startListening({ 
          continuous: true,
          language: 'es-ES'
        });
        console.log('✅ Escucha iniciada - Habla ahora...');
      } catch (error) {
        console.error('❌ Error al iniciar escucha:', error);
        alert('Error: ' + error.message);
      }
    }
  };

  // Función de envío automático
  const sendMessageAuto = () => {
    const text = inputText.trim();
    
    if (!loading && !message && text) {
      
      console.log('📤 Auto-enviando:', text);
      chat(text);
      setInputText("");
      resetTranscript();
      
      // NO detener el listening - sigue escuchando
      console.log('🎤 Micrófono sigue activo - Puedes seguir hablando...');
    }
  };

  // Función de envío manual
  const sendMessage = () => {
    const text = inputText || input.current.value;
    
    if (!loading && !message && text.trim()) {
      setAnimationChat("Searching")
      chat(text);
      setInputText("");
      input.current.value = "";
      resetTranscript();
      
      // Detener escucha al enviar manualmente
      if (listening) {
        SpeechRecognition.stopListening();
      }
      
      // Limpiar timer
      if (silenceTimerRef.current) {

        clearTimeout(silenceTimerRef.current);
      }
    }
  };

  if (hidden) {
    return null;
  }

  return (
    <>
      <div className="fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col pointer-events-none">
        <div className="w-full flex flex-col items-end justify-center gap-4">
          <button
            onClick={() => setCameraZoomed(!cameraZoomed)}  // aquí se está revissando el tema del cambio de posición de camara con respecto del visor
            className="pointer-events-auto bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-md"
          >
            {cameraZoomed ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
              </svg>
            )}
          </button>
          <button
            onClick={() => {
              const body = document.querySelector("body");
              body.classList.toggle("greenScreen");
            }}
            className="pointer-events-auto bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-md"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </button>
        </div>
        <div className="flex items-center gap-2 pointer-events-auto max-w-screen-sm w-full mx-auto">
          <input
            className="w-full placeholder:text-gray-800 placeholder:italic p-4 rounded-md bg-opacity-50 bg-white backdrop-blur-md"
            placeholder={listening ? "🎤 Escuchando..." : "Escribe un mensaje o usa el micrófono..."}
            ref={input}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <button
            disabled={loading || message}
            onClick={sendMessage}
            className={`bg-blue-500 hover:bg-blue-600 text-white p-4 px-10 font-semibold uppercase rounded-md ${
              loading || message ? "cursor-not-allowed opacity-30" : ""
            }`}
          >
            Enviar
          </button>

          <button
            onClick={handleMicClick}
            disabled={!browserSupportsSpeechRecognition || micPermission === false}
            className={`text-white p-4 rounded-md flex items-center justify-center
              ${listening ? "bg-red-600 animate-pulse" : "bg-red-500 hover:bg-red-600"}
              ${(!browserSupportsSpeechRecognition || micPermission === false) ? "opacity-50 cursor-not-allowed" : ""}
            `}
            title={
              !browserSupportsSpeechRecognition 
                ? "Usa Google Chrome"
                : micPermission === false
                  ? "Micrófono bloqueado"
                  : listening 
                    ? "Detener grabación" 
                    : "Iniciar grabación"
            }
          >
            {listening ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
                <circle cx="12" cy="12" r="6" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
                <path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3z" />
                <path strokeWidth="1.5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 11-14 0M12 18v3m0 0h3m-3 0H9" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </>
  );
};
