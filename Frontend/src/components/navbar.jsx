import { NavLink } from "react-router-dom";

export function Navbar() {
  const linkClass =
    "rounded-full px-3 py-1.5 md:px-6 md:py-2 hover:bg-white/10 transition text-xs md:text-base lg:text-xl";

  const activeClass =
    "border-2 border-white";

  return (
    <nav className="w-full bg-[#0f2c63] text-white px-2 md:px-6 py-2 md:py-4 flex justify-center space-x-2 md:space-x-8 lg:space-x-14 font-medium">
      <NavLink
        to="/sobre"
        className={({ isActive }) =>
          `${linkClass} ${isActive ? activeClass : ""}`
        }
      >
        Sobre
      </NavLink>

      <NavLink
        to="/llm"
        className={({ isActive }) =>
          `${linkClass} ${isActive ? activeClass : ""}`
        }
      >
        <span className="hidden md:inline">Agente LLM</span>
        <span className="md:hidden">LLM</span>
      </NavLink>

      <NavLink
        to="/entrenamiento"
        className={({ isActive }) =>
          `${linkClass} ${isActive ? activeClass : ""}`
        }
      >
        <span className="hidden sm:inline">Entrenamiento</span>
        <span className="sm:hidden">Entrenar</span>
      </NavLink>
    </nav>
  );
}