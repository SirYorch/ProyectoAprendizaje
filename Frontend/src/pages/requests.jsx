import { useState } from "react";
import { ImageInput } from "@/components/ui/image-input";
import { Upload, Loader2, CheckCircle2 } from "lucide-react";

export function Requests() {
    const URL_Link = "http://localhost:5000";
    const [image, setImage] = useState(null);
    const [label, setLabel] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");

    const handleTrain = async () => {
        if (!image || !label.trim()) return;

        setLoading(true);
        setResult(null);
        setError("");

        const formData = new FormData();
        formData.append("image", image);
        formData.append("label", label);

        try {
            const response = await fetch(`${URL_Link}/train`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Training failed");
            }

            const data = await response.json();
            setResult(data.message || 'Modelo actualizado exitosamente');
            
            // Limpiar formulario después de éxito
            setImage(null);
            setLabel("");

        } catch (error) {
            console.error(error);
            setError("Error al entrenar el modelo. Por favor, intenta nuevamente.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !loading && image && label.trim()) {
            handleTrain();
        }
    };

    return (
        <div className="h-[calc(90vh-8px)] overflow-hidden bg-[#f5f6f8]">
            {/* Línea superior */}
            <div className="border-b-8 border-[#ffb703] w-full"></div>

            {/* CONTENEDOR PRINCIPAL */}
            <div className="flex flex-col items-center px-6 pt-6 text-[#0f2c63] h-[calc(80vh-8px)]">
                
                <div className="text-3xl font-semibold mb-4">
                    Entrenamiento del Modelo
                </div>

                {/* Caja principal de contenido */}
                <div className="w-full md:w-11/12 lg:w-10/12 xl:w-8/12 flex-1 overflow-y-auto px-8 py-8 bg-white rounded-2xl shadow-md border border-[#0f2c63]/20 mb-4">
                    
                    <p className="text-lg text-[#0f2c63]/70 mb-8 text-center">
                        Sube una imagen con su etiqueta para entrenar el modelo de reconocimiento.
                    </p>

                    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
                        
                        {/* Input de imagen */}
                        <div>
                            <label className="block text-lg font-medium mb-3 text-[#0f2c63]">
                                Imagen del Producto
                            </label>
                            <ImageInput onChange={setImage} />
                        </div>

                        {/* Input de etiqueta */}
                        <div>
                            <label className="block text-lg font-medium mb-3 text-[#0f2c63]">
                                Etiqueta del Producto
                            </label>
                            <input
                                type="text"
                                placeholder="Ejemplo: laptop_dell, mouse_logitech..."
                                value={label}
                                onChange={(e) => setLabel(e.target.value)}
                                onKeyDown={handleKeyDown}
                                disabled={loading}
                                className="w-full border-2 border-[#0f2c63] rounded-full px-6 py-3 text-lg outline-none focus:border-[#ffb703] transition disabled:opacity-50 disabled:cursor-not-allowed"
                            />
                        </div>

                        {/* Botón de entrenar */}
                        <button
                            onClick={handleTrain}
                            disabled={!image || !label.trim() || loading}
                            className="w-full bg-[#0f2c63] text-white px-6 py-4 rounded-full text-xl font-medium hover:bg-[#0d2452] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 mt-4"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                    Entrenando modelo...
                                </>
                            ) : (
                                <>
                                    <Upload className="w-6 h-6" />
                                    Entrenar Modelo
                                </>
                            )}
                        </button>

                        {/* Resultado exitoso */}
                        {result && (
                            <div className="flex items-center gap-3 p-4 rounded-2xl bg-[#ffb703]/20 border-2 border-[#ffb703] text-[#0f2c63] animate-in fade-in slide-in-from-bottom-4">
                                <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
                                <p className="font-medium text-lg">{result}</p>
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="p-4 rounded-2xl bg-red-50 border-2 border-red-300 text-red-700 text-center">
                                <p className="font-medium">{error}</p>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}