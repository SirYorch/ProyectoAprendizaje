import { NavLink } from "react-router-dom";

export function Navbar() {
  const linkClass =
    "rounded-full px-6 py-2 hover:bg-white/10 transition";

  const activeClass =
    "border-2 border-white";

  return (
    <nav className="w-full bg-[#0f2c63] text-white px-6 py-4 flex justify-center space-x-14 text-xl font-medium">
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
        Agente LLM
      </NavLink>

      <NavLink
        to="/metodos"
        className={({ isActive }) =>
          `${linkClass} ${isActive ? activeClass : ""}`
        }
      >
        Métodos
      </NavLink>
    </nav>
  );
}
