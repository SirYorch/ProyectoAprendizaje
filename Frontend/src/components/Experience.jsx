import {
  CameraControls,
  ContactShadows,
  Environment,
  Text,
} from "@react-three/drei";
import { Suspense, useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { Avatar } from "./Avatar";

const Dots = (props) => {
  const { loading } = useChat();
  const [loadingText, setLoadingText] = useState("");
  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setLoadingText((loadingText) => {
          if (loadingText.length > 2) {
            return ".";
          }
          return loadingText + ".";
        });
      }, 800);
      return () => clearInterval(interval);
    } else {
      setLoadingText("");
    }
  }, [loading]);
  if (!loading) return null;
  return (
    <group {...props}>
      <Text fontSize={0.14} anchorX={"left"} anchorY={"bottom"}>
        {loadingText}
        <meshBasicMaterial attach="material" color="black" />
      </Text>
    </group>
  );
};

export const Experience = () => {
  const cameraControls = useRef();
  const { cameraZoomed } = useChat();

  useEffect(() => {
    cameraControls.current.setLookAt(0.2, 1.5, 2, 0, 1.5, -1, true);
  }, []);

  useEffect(() => {
    if (cameraZoomed) {
      cameraControls.current.setLookAt(0, 1.9, 2.5, 0, 1, -1, true);
    } else {
      cameraControls.current.setLookAt(0.2, 1.5, 2, 0, 1.5, -1, true);
    }
  }, [cameraZoomed]);
  return (
  <>
    <CameraControls ref={cameraControls}  makeDefault  mouseButtons={{ left: 0, middle: 0, right: 0 }}/>
    <Environment preset="sunset" />
    <Suspense>
      {/* camera={{ position: [0, 0, 1], fov: 30 }} */}
      <Dots position-y={1.75} position-x={-0.02} />
    </Suspense>
    <Avatar />
    <ContactShadows opacity={0.7} />
  </>
);
};