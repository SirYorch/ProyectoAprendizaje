import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:3000";


const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  
  const chat = async (message) => {
    setLoading(true);
    console.log("datos enviador = " +message)
    const data = await fetch(`${backendUrl}/chat/test`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });


    const resp = (await data.json()).messages;
    console.log(resp)
    setMessages((messages) => [...messages, ...resp]);
    setLoading(false);
  };
  
  

  const setAnimationChat = async (animationName) => {
    setLoading(true);

    const forcedMessage = {
      text: "",               // opcional, si no quieres mostrar texto
      audio: null,            // si no hay audio
      lipsync: null,          // si no hay lipsync
      facialExpression: "default",
      animation: animationName,
    };
    const it = [forcedMessage]
    console.log(it)
    // Esto disparará el useEffect del Avatar
    setMessage(forcedMessage)
    setLoading(false);

    return forcedMessage;
  };

  
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
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
