import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/navbar";
import { Home } from "./pages/home";
import { Llm } from "./pages/llm";
import { Requests } from "./pages/requests";
import { Leva } from "leva";

function App() {
  return (
    <>
      {/* <Loader /> */}
      <Leva hidden/>
      <BrowserRouter>

        <Navbar />

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/sobre" element={<Home />} />
          {/* luego crearás las otras */}
          <Route path="/llm" element={<Llm />} />
          <Route path="/entrenamiento" element={<Requests/>} />
        </Routes>
      </BrowserRouter>
{/* 
      <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
        <Experience />
      </Canvas> */}
    </>
  );
}

// function App() {

//   const avatarRef = useRef();


//   return (
//     <>
//       <Loader />
//       <Leva/>
//       <UI /> 
//       <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
//         <Experience />
//       </Canvas>
//     </>
//   );
// }

export default App;
