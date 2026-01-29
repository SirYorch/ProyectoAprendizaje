import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Llm } from "./pages/llm";
function App() {
  return (
    <>
      {/* <Loader /> */}
      <BrowserRouter>

        <Routes>
          <Route path="/" element={<Llm />} />
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
