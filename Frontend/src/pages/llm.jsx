import { useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

export function Llm() {
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");

  const { chat, loading, message } = useChat();

  useEffect(() => {
    if (message && message.text) {
      setMensajes((prev) => [
        ...prev,
        {
          remitente: "CHAT",
          texto: message.text,
          archivo: message.file || null,
        },
      ]);
    }
  }, [message]);

  const enviarMensaje = async () => {
    if (!texto.trim()) return;

    setMensajes((prev) => [...prev, { remitente: "me", texto }]);
    const msg = texto;
    setTexto("");
    setError("");

    try {
      await chat(msg);
    } catch {
      setError("Error al comunicarse con el servidor");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") enviarMensaje();
  };

  return (
    <div className="w-screen h-[90vh] overflow-hidden bg-[#f5f6f8] flex flex-col">

      

      {/* CONTENIDO */}
      <div className="flex-1 flex flex-col w-full px-6 pt-6 text-[#0f2c63]">

        <div className="text-3xl font-semibold mb-4">
          Hola, ¿en qué puedo ayudarte?
        </div>

        {/* CHAT */}
        <div className="w-full flex-1 overflow-y-auto px-4 py-6 bg-white rounded-2xl shadow-md border border-[#0f2c63]/20 mb-4">

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
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                    >
                      {m.texto}
                    </ReactMarkdown>

                    {m.archivo && (
                      <div className="mt-2 flex items-center gap-2 text-sm bg-white/30 rounded-lg px-3 py-2">
                        <span>✓ Archivo descargado: {m.archivo.name}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

            </div>
          ))}

          {loading && (
            <div className="text-center mt-4 animate-pulse">
              Pensando...
            </div>
          )}

          {error && (
            <div className="text-center text-red-500 mt-4">
              {error}
            </div>
          )}

        </div>

        {/* INPUT */}
        <div className="flex w-full gap-4 pb-4">
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
            className="bg-[#0f2c63] text-white px-6 py-3 rounded-full text-xl hover:bg-[#0d2452] transition disabled:opacity-50"
          >
            Enviar
          </button>
        </div>

      </div>
    </div>
  );
}
