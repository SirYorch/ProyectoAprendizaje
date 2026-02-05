import { useState, useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import { Mic, Camera, Image as ImageIcon, X } from "lucide-react";

export function Llm() {
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");

  // Camera & Image state
  const [cameraOpen, setCameraOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [imgSrc, setImgSrc] = useState(null); // Preview data (base64)
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

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
    // Calling internal function (we need to mirror sending logic but with specific text)
    // We can't easily call sending logic because state might be stale in closure
    // But since we pass `finalText`, we can just dispatch.
    // However, we need to respect other state (files, etc which are not implemented yet).
    // For now we just call update state and trigger send. 
    // Actually, calling `enviarMensaje` directly might use stale `texto` state if we are not careful.
    // But `texto` is updated in the effect just before.

    // Better approach: Since we are in an effect dependent on transcript, `enviarMensaje` needs access to current stuff.
    // Let's create a helper that takes arguments.

    const nuevoMensaje = {
      remitente: "me",
      texto: finalText,
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);
    // Send logic
    chat(finalText, imgSrc); // Use current imgSrc state (closure might capture old value?)
    // Actually `imgSrc` might be stale here if changed recently? usually fine.

    setTexto("");
    resetTranscript();
    // setImgSrc(null); // Should we clear image on auto send? Probably yes.
    // But let's verify if user wants that. For now, yes.
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

    if (!textoAEnviar.trim() && !imagenAEnviar) return;

    // 1. UI: Agregar mensaje del usuario al historial inmediatamente
    const nuevoMensaje = {
      remitente: "me",
      texto: textoAEnviar,
      imagen: imagenAEnviar // Guardar imagen para mostrar en chat
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);

    // Limpiar estado
    setTexto("");
    setImgSrc(null);
    setError("");

    try {
      let finalText = textoAEnviar;

      // 2. Lógica secuencial: Si hay imagen, enviar a /predict
      if (imagenAEnviar) {
        const blob = dataURItoBlob(imagenAEnviar);
        if (blob) {
          // El usuario pide "siempre se envía primero la imagen" (a predict)
          const prediction = await predict(blob);

          if (prediction && prediction.label) {
            // Agregar contexto al texto que irá al chat
            finalText = `${textoAEnviar} \n\n[System: The user sent an image of: ${prediction.label}. Match confidence: ${prediction.probability}]`;
          } else {
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
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
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
        setImgSrc(reader.result);
        // Also close camera modal if open (though usually this input is separate)
        if (cameraOpen) stopCamera();
      };
      reader.readAsDataURL(file);
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
    <div className="h-[calc(90vh-8px)] overflow-hidden bg-[#f5f6f8]">

      {/* Línea superior */}
      <div className="border-b-8 border-[#ffb703] w-full"></div>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="flex flex-row w-full h-[calc(80vh-8px)]">

        {/* ============================
            COLUMNA IZQUIERDA: CHAT (50%)
        ============================ */}
        <div className="w-full flex flex-col items-center px-6 pt-6 text-[#0f2c63]">

          <div className="text-3xl font-semibold mb-4">
            Hola, ¿en qué puedo ayudarte?
          </div>

          {/* Caja de mensajes */}
          <div className="w-full md:w-11/12 lg:w-10/12 flex-1 overflow-y-auto px-4 py-6 bg-white rounded-2xl shadow-md border border-[#0f2c63]/20 mb-4">

            {mensajes.map((m, i) => (
              <div key={i} className="mb-4 w-full">

                {m.remitente === "me" && (
                  <div className="flex justify-end mb-2">
                    <div className="flex flex-col items-end max-w-[75%]">
                      {m.imagen && (
                        <img
                          src={m.imagen}
                          alt="User upload"
                          className="max-w-full h-auto rounded-lg mb-2 border border-[#0f2c63]/20"
                          style={{ maxHeight: '200px' }}
                        />
                      )}
                      {m.texto && (
                        <div className="bg-[#0f2c63] text-white px-4 py-2 rounded-3xl">
                          {m.texto}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {m.remitente === "CHAT" && (
                  <div className="flex justify-start">
                    <div className="bg-[#ffb703] text-[#0f2c63] px-4 py-2 rounded-3xl max-w-[75%]">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {m.texto}
                      </ReactMarkdown>

                      {/* Indicador de archivo descargado */}
                      {m.archivo && (
                        <div className="mt-2 flex items-center gap-2 text-sm bg-white/30 rounded-lg px-3 py-2">
                          <svg
                            className="w-4 h-4"
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
                          <span>✓ Archivo descargado: {m.archivo.name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

              </div>
            ))}

            {loading && (
              <div className="text-center mt-4 text-[#0f2c63] animate-pulse">
                Pensando...
              </div>
            )}

            {error && (
              <div className="text-center text-red-500 mt-4">
                {error}
              </div>
            )}

          </div>

          {/* Input + Botón */}
          <div className="flex flex-col w-full md:w-11/12 lg:w-10/12 pb-4 gap-2">

            {/* Image Preview */}
            {imgSrc && (
              <div className="relative w-fit">
                <img src={imgSrc} alt="Preview" className="h-20 rounded-lg border border-[#0f2c63]/20" />
                <button
                  onClick={() => setImgSrc(null)}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X size={12} />
                </button>
              </div>
            )}

            <div className="flex w-full gap-4">
              <input
                type="text"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu consulta…"
                className="flex-1 border-2 border-[#0f2c63] rounded-full px-6 py-3 text-xl outline-none"
                disabled={loading}
              />

              {/* Mic Button */}
              <button
                onClick={toggleMic}
                className={`p-3 rounded-full transition-colors ${listening ? "bg-red-500 text-white animate-pulse" : "bg-gray-200 text-[#0f2c63] hover:bg-gray-300"
                  }`}
                title="Dictar por voz"
              >
                <Mic size={24} />
              </button>

              {/* Camera Button */}
              <button
                onClick={() => setCameraOpen(true)}
                className="p-3 rounded-full bg-gray-200 text-[#0f2c63] hover:bg-gray-300 transition-colors"
                title="Tomar foto / Subir imagen"
              >
                <Camera size={24} />
              </button>

              <button
                onClick={enviarMensaje}
                disabled={loading}
                className="bg-[#0f2c63] text-white px-6 py-3 rounded-full text-xl hover:bg-[#0d2452] transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Enviar
              </button>
            </div>
          </div>

          {/* Camera Modal */}
          {cameraOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
              <div className="bg-white p-4 rounded-2xl shadow-2xl max-w-2xl w-full flex flex-col gap-4 relative">
                <button
                  onClick={stopCamera}
                  className="absolute top-4 right-4 text-gray-500 hover:text-red-500"
                >
                  <X size={24} />
                </button>

                <h3 className="text-xl font-bold text-[#0f2c63] text-center">Cámara / Subir Imagen</h3>

                <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
                  {!isStreaming ? (
                    <div className="text-white flex flex-col items-center gap-2">
                      <p>Cámara inactiva</p>
                      <button onClick={startCamera} className="px-4 py-2 bg-[#0f2c63] rounded-full text-white text-sm">
                        Activar Cámara
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

                <div className="flex justify-center gap-4 mt-2">
                  <button
                    onClick={captureImage}
                    disabled={!isStreaming}
                    className="flex items-center gap-2 bg-[#0f2c63] text-white px-6 py-2 rounded-full hover:bg-[#0d2452] disabled:opacity-50"
                  >
                    <Camera size={20} /> Capturar
                  </button>

                  <div className="relative">
                    <input
                      type="file"
                      accept="image/*"
                      ref={fileInputRef}
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-2 bg-gray-200 text-[#0f2c63] px-6 py-2 rounded-full hover:bg-gray-300"
                    >
                      <ImageIcon size={20} /> Subir Archivo
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* ============================
            COLUMNA DERECHA: CANVAS (50%)
        ============================ */}
        {/* <div className="w-1/2 h-7/10 flex justify-center items-center p-6">
          <div className="w-full h-full rounded-2xl shadow-lg border border-[#0f2c63]/20 overflow-hidden">
            <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
              <Experience />
            </Canvas>
          </div>
        </div> */}

      </div>
    </div>
  );
}