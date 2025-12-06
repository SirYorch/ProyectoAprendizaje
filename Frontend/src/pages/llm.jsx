import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Experience } from "../components/Experience";
// import ReactMarkdown from "react-markdown";

export function Llm() {
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const enviarMensaje = () => {
    if (!texto.trim()) return;

    const nuevoMensaje = {
      remitente: "me",
      texto,
    };

    setMensajes((prev) => [...prev, nuevoMensaje]);
    setTexto("");
    setError("");
    setLoading(true);

    setTimeout(() => {
      const respuesta = {
        remitente: "CHAT",
        texto: "Respuesta automática del bot: **Hola!**\n\nEsto es Markdown 😉",
      };

      setMensajes((prev) => [...prev, respuesta]);
      setLoading(false);
    }, 1200);
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
    <div className="w-1/2 flex flex-col items-center px-6 pt-6 text-[#0f2c63]">

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
                  <ReactMarkdown>{m.texto}</ReactMarkdown>
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
        />
        <button
          onClick={enviarMensaje}
          className="bg-[#0f2c63] text-white px-6 py-3 rounded-full text-xl hover:bg-[#0d2452] transition"
        >
          Enviar
        </button>
      </div>

    </div>

    {/* ============================
        COLUMNA DERECHA: CANVAS (50%)
    ============================ */}
    <div className="w-1/2 h-7/10 flex justify-center items-center p-6">
      <div className="w-full h-full rounded-2xl shadow-lg border border-[#0f2c63]/20 overflow-hidden">
        <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
          <Experience />
        </Canvas>
      </div>
    </div>

  </div>
</div>

  );
}
