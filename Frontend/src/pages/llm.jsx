import { useState, useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import { Mic, Camera, Image as ImageIcon, X, Video, Circle, Square } from "lucide-react";

// const backendUrl = import.meta.env.VITE_API_URL || "https://6wnwj9t1-5000.brs.devtunnels.ms";
const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";

export function Llm() {
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");

  // Camera & Image state
  const [cameraOpen, setCameraOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [imgSrc, setImgSrc] = useState(null); // Preview data (base64)
  const [videoSrc, setVideoSrc] = useState(null); // Video preview data
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);
  const videoFileInputRef = useRef(null);

  // Speech Recognition
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  // Timer for auto-send on silence
  const silenceTimer = useRef(null);

  // Usar el hook useChat
  const { chat, predict, loading, message } = useChat();

  // Helper to convert dataURI to Blob
  const dataURItoBlob = (dataURI) => {
    try {
      const byteString = atob(dataURI.split(',')[1]);
      const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
      }
      return new Blob([ab], { type: mimeString });
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  // Escuchar cambios en 'message' para agregar respuestas del bot al chat
  useEffect(() => {
    if (message && message.text) {
      const respuestaBot = {
        remitente: "CHAT",
        texto: message.text,
        archivo: message.file || null // Guardar info del archivo si existe
      };
      setMensajes((prev) => [...prev, respuestaBot]);
    }
  }, [message]);

  // Sync transcript to input
  useEffect(() => {
    if (listening) {
      setTexto(transcript);

      // Reset silence timer on every transcript change
      if (silenceTimer.current) clearTimeout(silenceTimer.current);

      // Set new timer: if 2000ms pass without change, stop & send
      silenceTimer.current = setTimeout(() => {
        if (transcript.trim().length > 0) {
          SpeechRecognition.stopListening();
          handleAutoSend(transcript);
        }
      }, 2000);
    }
  }, [transcript, listening]);

  const handleAutoSend = (finalText) => {
    const nuevoMensaje = {
      remitente: "me",
      texto: finalText,
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);
    // Send logic
    chat(finalText, imgSrc);

    setTexto("");
    resetTranscript();
  };


  const enviarMensaje = async (arg1 = null, arg2 = null) => {
    // Handle arguments: if arg1 is an event (object) or null, treat as default send. 
    // If arg1 is string, treat as text override.
    let textoOverride = null;
    let imageOverride = null;

    if (typeof arg1 === 'string') {
      textoOverride = arg1;
      imageOverride = arg2;
    }

    const textoAEnviar = textoOverride !== null ? textoOverride : texto;
    const imagenAEnviar = imageOverride !== null ? imageOverride : imgSrc;
    const videoAEnviar = videoSrc;

    if (!textoAEnviar.trim() && !imagenAEnviar && !videoAEnviar) return;

    // 1. UI: Agregar mensaje del usuario al historial inmediatamente
    const nuevoMensaje = {
      remitente: "me",
      texto: textoAEnviar,
      imagen: imagenAEnviar, // Guardar imagen para mostrar en chat
      video: videoAEnviar // Guardar video para mostrar en chat
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);

    // Limpiar estado
    setTexto("");
    setImgSrc(null);
    setVideoSrc(null);
    setError("");

    try {
      let finalText = textoAEnviar;

      // 2. Lógica secuencial: Si hay video, enviar a /video
      if (videoAEnviar) {
        const blob = dataURItoBlob(videoAEnviar);
        if (blob) {
          const formData = new FormData();
          formData.append('video', blob, 'recording.webm');

          try {
            const response = await fetch(`${backendUrl}/video`, {
              method: 'POST',
              body: formData,
            });

            if (response.ok) {
              const data = await response.json();
              setMensajes((prev) => [...prev, {
                remitente: "CHAT",
                texto: `🎥 **Video procesado exitosamente**`
              }]);
              finalText = `${textoAEnviar} \n\n[System: The user sent a video]`;
            } else {
              setMensajes((prev) => [...prev, {
                remitente: "CHAT",
                texto: `⚠️ Error al procesar el video.`
              }]);
            }
          } catch (err) {
            console.error("Error uploading video:", err);
          }
        }
      }
      // Si hay imagen, enviar a /predict
      else if (imagenAEnviar) {
        const blob = dataURItoBlob(imagenAEnviar);
        if (blob) {
          // El usuario pide "siempre se envía primero la imagen" (a predict)
          const prediction = await predict(blob);

          if (prediction && prediction.label) {
            // Mostrar resultado en el chat
            console.log(prediction);
            setMensajes((prev) => [...prev, {
              remitente: "CHAT",
              texto: `🔍 **Resultado de análisis:**\n\n**Objeto:** ${prediction.label}\n**Matches:** ${(prediction.matches)}`
            }]);

            // Agregar contexto al texto que irá al chat
            finalText = `${textoAEnviar} \n\n[System: The user sent an image of: ${prediction.label}.`;
          } else {
            setMensajes((prev) => [...prev, {
              remitente: "CHAT",
              texto: `⚠️ No se pudo identificar el objeto en la imagen.`
            }]);
            finalText = `${textoAEnviar} \n\n[System: The user sent an image but it could not be identified]`;
          }
        }
      }

      // 3. Luego el texto se envía "a donde se estaba enviando" (Chat API)
      await chat(finalText);

    } catch (err) {
      console.error("Error al enviar mensaje:", err);
      setError("Error al comunicarse con el servidor");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") enviarMensaje();
  };

  // --- Camera & Image Handlers ---

  const startCamera = async () => {
    try {
      setCameraOpen(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment"
        }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      } else {
        // Cleaning up if ref is missing (e.g. modal closed fast)
        stream.getTracks().forEach(t => t.stop());
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("No se pudo acceder a la cámara. Verifique los permisos.");
      setCameraOpen(false);
      setIsStreaming(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraOpen(false);
    setIsStreaming(false);
  };

  const captureImage = () => {
    if (videoRef.current) {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoRef.current, 0, 0);
      const dataUrl = canvas.toDataURL("image/png");
      setImgSrc(dataUrl);
      stopCamera();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (file.type.startsWith('video/')) {
          setVideoSrc(reader.result);
        } else {
          setImgSrc(reader.result);
        }
        // Also close camera modal if open (though usually this input is separate)
        if (cameraOpen) stopCamera();
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setVideoSrc(reader.result);
        if (cameraOpen) stopCamera();
      };
      reader.readAsDataURL(file);
    }
  };

  const startVideoRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: true
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);

        const recorder = new MediaRecorder(stream, {
          mimeType: 'video/webm;codecs=vp8,opus'
        });

        const chunks = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data);
          }
        };

        recorder.onstop = () => {
          const blob = new Blob(chunks, { type: 'video/webm' });
          const reader = new FileReader();
          reader.onloadend = () => {
            setVideoSrc(reader.result);
            stopCamera();
          };
          reader.readAsDataURL(blob);
        };

        setMediaRecorder(recorder);
        recorder.start();
        setIsRecording(true);
      }
    } catch (err) {
      console.error("Error starting video recording:", err);
      alert("No se pudo acceder a la cámara/micrófono. Verifique los permisos.");
    }
  };

  const stopVideoRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Toggle Mic
  const toggleMic = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true, language: 'es-ES' });
    }
  };

  return (
    <div className="h-screen md:h-[calc(90vh-8px)] overflow-hidden bg-[#f5f6f8] flex flex-col">

      {/* Línea superior */}
      <div className="border-b-4 md:border-b-8 border-[#ffb703] w-full shrink-0"></div>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="flex flex-col md:flex-row w-full flex-1 overflow-hidden">

        {/* ============================
            COLUMNA IZQUIERDA: CHAT (Full Width on Mobile)
        ============================ */}
        <div className="w-full h-full flex flex-col items-center px-2 pt-2 md:px-6 md:pt-6 text-[#0f2c63]">

          <div className="hidden md:block text-2xl md:text-3xl font-semibold mb-3 md:mb-4 text-center">
            Hola, ¿en qué puedo ayudarte?
          </div>
          {/* Mobile Header - Compact */}
          <div className="md:hidden w-full text-center py-2 font-bold text-sm text-[#0f2c63]">
            Asistente Virtual
          </div>

          {/* Caja de mensajes */}
          <div className="w-full md:w-11/12 lg:w-10/12 flex-1 overflow-y-auto px-2 py-2 md:px-4 md:py-6 bg-white rounded-lg md:rounded-2xl shadow-sm md:shadow-md border border-[#0f2c63]/20 mb-2 md:mb-4 scroll-smooth">

            {mensajes.map((m, i) => (
              <div key={i} className="mb-2 md:mb-4 w-full">

                {m.remitente === "me" && (
                  <div className="flex justify-end mb-1 md:mb-2">
                    <div className="flex flex-col items-end max-w-[85%] md:max-w-[75%]">
                      {m.imagen && (
                        <img
                          src={m.imagen}
                          alt="User upload"
                          className="max-w-full h-auto rounded-lg mb-1 md:mb-2 border border-[#0f2c63]/20"
                          style={{ maxHeight: '120px', objectFit: 'contain' }}
                        />
                      )}
                      {m.video && (
                        <video
                          src={m.video}
                          controls
                          className="max-w-full h-auto rounded-lg mb-1 md:mb-2 border border-[#0f2c63]/20"
                          style={{ maxHeight: '120px', objectFit: 'contain' }}
                        />
                      )}
                      {m.texto && (
                        <div className="bg-[#0f2c63] text-white px-3 py-1.5 md:px-4 md:py-2 rounded-2xl md:rounded-3xl text-xs md:text-base break-words">
                          {m.texto}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {m.remitente === "CHAT" && (
                  <div className="flex justify-start">
                    <div className="bg-[#ffb703] text-[#0f2c63] px-3 py-1.5 md:px-4 md:py-2 rounded-2xl md:rounded-3xl max-w-[85%] md:max-w-[75%] text-xs md:text-base break-words">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {m.texto}
                      </ReactMarkdown>

                      {/* Indicador de archivo descargado */}
                      {m.archivo && (
                        <div className="mt-2 flex items-center gap-2 text-xs bg-white/30 rounded-lg px-2 py-1 md:px-3 md:py-2">
                          <svg
                            className="w-3 h-3 md:w-4 md:h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <span className="truncate max-w-[120px] md:max-w-xs">✓ {m.archivo.name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

              </div>
            ))}

            {loading && (
              <div className="text-center mt-2 md:mt-4 text-[#0f2c63] animate-pulse text-xs md:text-sm">
                Pensando...
              </div>
            )}

            {error && (
              <div className="text-center text-red-500 mt-2 md:mt-4 text-xs md:text-sm">
                {error}
              </div>
            )}

          </div>

          {/* Input + Botón - Compact container */}
          <div className="flex flex-col w-full md:w-11/12 lg:w-10/12 pb-2 md:pb-4 gap-2 shrink-0">

            {/* Image Preview */}
            {imgSrc && (
              <div className="relative w-fit mx-auto md:mx-0">
                <img src={imgSrc} alt="Preview" className="h-12 md:h-20 rounded-lg border border-[#0f2c63]/20" />
                <button
                  onClick={() => setImgSrc(null)}
                  className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X size={10} className="md:w-3 md:h-3" />
                </button>
              </div>
            )}

            {/* Video Preview */}
            {videoSrc && (
              <div className="relative w-fit mx-auto md:mx-0">
                <video src={videoSrc} controls className="h-20 md:h-32 rounded-lg border border-[#0f2c63]/20" />
                <button
                  onClick={() => setVideoSrc(null)}
                  className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X size={10} className="md:w-3 md:h-3" />
                </button>
              </div>
            )}

            <div className="flex w-full gap-1.5 md:gap-2 items-center">
              <input
                type="text"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe..."
                className="flex-1 border border-[#0f2c63] rounded-full px-3 py-1.5 md:px-6 md:py-3 text-xs md:text-base lg:text-xl outline-none min-w-0"
                disabled={loading}
              />

              {/* Mic Button - Smaller on mobile */}
              <button
                onClick={toggleMic}
                className={`p-1.5 md:p-3 rounded-full transition-colors shrink-0 ${listening ? "bg-red-500 text-white animate-pulse" : "bg-gray-200 text-[#0f2c63] hover:bg-gray-300"
                  }`}
                title="Dictar"
              >
                <Mic size={16} className="md:w-6 md:h-6" />
              </button>

              {/* Camera Button - Smaller on mobile */}
              <button
                onClick={() => setCameraOpen(true)}
                className="p-1.5 md:p-3 rounded-full bg-gray-200 text-[#0f2c63] hover:bg-gray-300 transition-colors shrink-0"
                title="Cámara"
              >
                <Camera size={16} className="md:w-6 md:h-6" />
              </button>

              {/* Video Upload Button */}
              <button
                onClick={() => videoFileInputRef.current?.click()}
                className="p-1.5 md:p-3 rounded-full bg-gray-200 text-[#0f2c63] hover:bg-gray-300 transition-colors shrink-0"
                title="Subir Video"
              >
                <Video size={16} className="md:w-6 md:h-6" />
              </button>
              <input
                type="file"
                accept="video/*"
                ref={videoFileInputRef}
                className="hidden"
                onChange={handleVideoFileUpload}
              />

              <button
                onClick={enviarMensaje}
                disabled={loading}
                className="bg-[#0f2c63] text-white px-3 py-1.5 md:px-6 md:py-3 rounded-full text-xs md:text-base lg:text-xl hover:bg-[#0d2452] transition disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              >
                Enviar
              </button>
            </div>
          </div>

          {/* Camera Modal - Fullscreen on mobile */}
          {cameraOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-2 md:p-4">
              <div className="bg-white p-3 md:p-4 rounded-xl md:rounded-2xl shadow-2xl w-full max-w-sm md:max-w-2xl flex flex-col gap-2 md:gap-4 relative max-h-[90vh]">
                <button
                  onClick={stopCamera}
                  className="absolute top-2 right-2 md:top-4 md:right-4 text-gray-500 hover:text-red-500 bg-white rounded-full p-1 z-10"
                >
                  <X size={18} className="md:w-6 md:h-6" />
                </button>

                <h3 className="text-base md:text-xl font-bold text-[#0f2c63] text-center mt-1 md:mt-2">Cámara</h3>

                <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
                  {!isStreaming ? (
                    <div className="text-white flex flex-col items-center gap-2">
                      <p className="text-xs md:text-sm">Cámara inactiva</p>
                      <button onClick={startCamera} className="px-3 py-1.5 md:px-4 md:py-2 bg-[#0f2c63] rounded-full text-white text-xs md:text-sm">
                        Activar
                      </button>
                    </div>
                  ) : null}
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className={`w-full h-full object-cover ${!isStreaming ? 'hidden' : ''}`}
                  />
                </div>

                <div className="flex justify-center gap-2 mt-1 md:mt-2 flex-wrap">
                  <button
                    onClick={captureImage}
                    disabled={!isStreaming || isRecording}
                    className="flex items-center gap-1 md:gap-2 bg-[#0f2c63] text-white px-3 py-1.5 md:px-4 md:py-2 rounded-full hover:bg-[#0d2452] disabled:opacity-50 text-xs md:text-base"
                  >
                    <Camera size={14} className="md:w-5 md:h-5" /> Capturar Foto
                  </button>

                  {!isRecording ? (
                    <button
                      onClick={startVideoRecording}
                      disabled={isStreaming}
                      className="flex items-center gap-1 md:gap-2 bg-red-600 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-full hover:bg-red-700 disabled:opacity-50 text-xs md:text-base"
                    >
                      <Circle size={14} className="md:w-5 md:h-5" /> Grabar Video
                    </button>
                  ) : (
                    <button
                      onClick={stopVideoRecording}
                      className="flex items-center gap-1 md:gap-2 bg-red-600 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-full hover:bg-red-700 animate-pulse text-xs md:text-base"
                    >
                      <Square size={14} className="md:w-5 md:h-5" /> Detener
                    </button>
                  )}

                  <div className="relative">
                    <input
                      type="file"
                      accept="image/*,video/*"
                      capture="environment"
                      ref={fileInputRef}
                      className="hidden"
                      onChange={handleFileUpload}
                      id="file-upload"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-1 md:gap-2 bg-gray-200 text-[#0f2c63] px-3 py-1.5 md:px-4 md:py-2 rounded-full hover:bg-gray-300 text-xs md:text-base"
                    >
                      <ImageIcon size={14} className="md:w-5 md:h-5" /> Subir Archivo
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}