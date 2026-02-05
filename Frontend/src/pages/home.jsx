export function Home() {
  return (
    <div>
      <div className="bg-[#0f2c63] text-white pt-20 pb-20 md:pt-40 lg:pt-60 md:pb-40 lg:pb-60 px-4 md:px-6 text-center flex flex-col items-center justify-center">
        <h1 className="text-4xl md:text-6xl lg:text-9xl font-extrabold mb-4 md:mb-6 lg:mb-10">
          ProyectoAprendizaje
        </h1>

        <p className="text-2xl md:text-3xl lg:text-5xl font-semibold mb-3 md:mb-4 lg:mb-6">
          Productos cma
        </p>
        <p className="text-lg md:text-xl lg:text-2xl">
          Universidad Politécnica Salesiana
        </p>
      </div>

      <div className="border-b-4 md:border-b-6 lg:border-b-8 border-[#ffb703] w-full"></div>

      <div className="w-full flex flex-col md:flex-row justify-between items-center gap-4 md:gap-0 px-4 md:px-10 lg:px-20 pt-6 md:pt-10 lg:pt-16 text-[#0f2c63] bg-[#fff] text-base md:text-xl lg:text-3xl mb-0 pb-6 md:pb-0">
        <div className="text-center md:text-left">
          Cueva Jorge - Quito Karen - Barzallo Mateo
        </div>
        <div className="text-center md:text-right">
          Cuenca - Ecuador
        </div>
      </div>
    </div>
  );
}