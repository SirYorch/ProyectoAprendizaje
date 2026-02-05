import { useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { Experience } from "../components/Experience";
import { useChat } from "../hooks/useChat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

export function Llm() {
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");
  
  // Usar el hook useChat
  const { chat, loading, message } = useChat();

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

  const enviarMensaje = async () => {
    if (!texto.trim()) return;

    // Agregar mensaje del usuario
    const nuevoMensaje = {
      remitente: "me",
      texto,
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);
    const mensajeEnviado = texto;
    setTexto("");
    setError("");

    try {
      // Llamar al backend a través de useChat
      // El archivo se descargará automáticamente en el ChatContext
      await chat(mensajeEnviado);
      
    } catch (err) {
      console.error("Error al enviar mensaje:", err);
      setError("Error al comunicarse con el servidor");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") enviarMensaje();
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
                  <div className="flex justify-end">
                    <div className="bg-[#0f2c63] text-white px-4 py-2 rounded-3xl max-w-[75%]">
                      {m.texto}
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
          <div className="flex w-full md:w-11/12 lg:w-10/12 gap-4 pb-4">
            <input
              type="text"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu consulta…"
              className="flex-1 border-2 border-[#0f2c63] rounded-full px-6 py-3 text-xl outline-none"
              disabled={loading}
            />
            <button
              onClick={enviarMensaje}
              disabled={loading}
              className="bg-[#0f2c63] text-white px-6 py-3 rounded-full text-xl hover:bg-[#0d2452] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Enviar
            </button>
          </div>

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