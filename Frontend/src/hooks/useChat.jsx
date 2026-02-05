import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);

  const chat = async (message, image = null) => {
    setLoading(true);
    console.log("datos enviados = " + message);

    try {
      const data = await fetch(`${backendUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message, image }),
      });

      const response = await data.json();
      const resp = response.messages;

      console.log("Respuesta del backend:", resp);

      // Verificar si hay archivo en la respuesta
      if (resp[0]?.file) {
        console.log("✓ Archivo recibido:", resp[0].file.name);

        // Descargar el archivo automáticamente
        descargarArchivo(resp[0].file);
      }

      setMessages((messages) => [...messages, ...resp]);
    } catch (error) {
      console.error("Error en chat:", error);
    } finally {
      setLoading(false);
    }
  };

  const predict = async (fileBlob) => {
    try {
      const formData = new FormData();
      formData.append('image', fileBlob);

      const response = await fetch(`http://localhost:5000/predict`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Prediction request failed');
      }

      const data = await response.json();
      console.log("Prediction result:", data);
      return data;
    } catch (error) {
      console.error("Error in prediction:", error);
      return null;
    }
  };

  const descargarArchivo = (fileInfo) => {
    try {
      const { data: fileData, name: fileName, type: fileType } = fileInfo;

      // Convertir base64 a bytes
      const byteCharacters = atob(fileData);
      const byteNumbers = new Array(byteCharacters.length);

      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }

      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: fileType });

      // Crear URL temporal y descargar
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();

      // Limpiar
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log(`✓ Archivo descargado: ${fileName}`);
    } catch (err) {
      console.error("Error al descargar archivo:", err);
    }
  };

  const setAnimationChat = async (animationName) => {
    setLoading(true);

    const forcedMessage = {
      text: "",
      audio: null,
      lipsync: null,
      facialExpression: "default",
      animation: animationName,
    };

    const it = [forcedMessage];
    console.log(it);

    // Esto disparará el useEffect del Avatar
    setMessage(forcedMessage);
    setLoading(false);

    return forcedMessage;
  };

  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        predict,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
        setAnimationChat
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};