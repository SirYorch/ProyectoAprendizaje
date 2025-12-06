

export function Home() {
  return (
    <div>
      <div className="bg-[#0f2c63] text-white pt-60 pb-60 px-6 text-center flex flex-col items-center justify-center">
        <h1 className="text-9xl font-extrabold mb-10">Predicción Stock</h1>

        <p className="text-5xl font-semibold mb-6">Empresa de electrónicos</p>
        <p className="text-2xl">Universidad Politécnica Salesiana</p>
      </div>

      <div className="border-b-8 border-[#ffb703] w-full"></div>

      <div className="w-full flex justify-between items-center px-20 pt-12 pb-12 text-[#0f2c63] bg-[#fff] text-3xl mb-0 pb-0">
        <div>Cueva Jorge - Quito Karen - Barzallo Quito</div>
        <div>Cuenca - Ecuador</div>
      </div>
    </div>
  );
}
