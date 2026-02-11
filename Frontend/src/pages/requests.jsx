import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { ImageInput } from "@/components/ui/image-input";
import { Upload, Loader2, CheckCircle2, Trash2, Eye, History, Undo } from "lucide-react";

export function Requests() {
    // const URL_Link = "https://6wnwj9t1-5000.brs.devtunnels.ms";
    const URL_Link = import.meta.env.VITE_API_URL || "https://z16tt1w6-5000.use2.devtunnels.ms";
    // const URL_Link = "http://localhost:5000";
    const [image, setImage] = useState(null);
    const [label, setLabel] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
    const [markdownResult, setMarkdownResult] = useState(null);

    // Tuning State
    const [threshold, setThreshold] = useState(0.04);
    const [previewKeypointsImage, setPreviewKeypointsImage] = useState(null);
    const [keypointCount, setKeypointCount] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);

    // History State
    const [versions, setVersions] = useState([]);
    const [showHistory, setShowHistory] = useState(false);

    // Load versions
    const loadVersions = async () => {
        try {
            const res = await fetch(`${URL_Link}/mlflow/versions`);
            if (res.ok) {
                const data = await res.json();
                setVersions(data);
            }
        } catch (e) {
            console.error("Failed to load versions", e);
        }
    };

    useEffect(() => {
        if (showHistory) {
            loadVersions();
        }
    }, [showHistory]);

    const handleRestore = async (runId) => {
        if (!confirm("¿Estás seguro? Esto sobrescribirá la base de datos actual con esta versión.")) return;
        setLoading(true);
        try {
            const res = await fetch(`${URL_Link}/mlflow/restore`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ run_id: runId })
            });
            const data = await res.json();
            if (res.ok) {
                alert(data.message);
                loadVersions();
            } else {
                alert("Error: " + data.error);
            }
        } catch (e) {
            alert("Restauración fallida: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    // Load image preview
    useEffect(() => {
        if (image) {
            const reader = new FileReader();
            reader.onload = (e) => {
                if (e.target?.result) {
                    setImagePreview(e.target.result);
                }
            };
            reader.readAsDataURL(image);
        } else {
            setImagePreview(null);
            setPreviewKeypointsImage(null);
        }
    }, [image]);

    // Auto-preview when image is loaded
    useEffect(() => {
        if (image) {
            handlePreview();
        }
    }, [image]);

    const handlePreview = async () => {
        if (!image) return;
        setLoading(true);
        const formData = new FormData();
        formData.append("threshold", threshold.toString());
        formData.append("image", image);

        try {
            const res = await fetch(`${URL_Link}/preview_keypoints`, {
                method: "POST",
                body: formData
            });
            if (!res.ok) {
                try {
                    const err = await res.json();
                    throw new Error(err.error || "Error del servidor");
                } catch {
                    throw new Error(`Solicitud fallida con estado ${res.status}`);
                }
            }
            const data = await res.json();
            if (data.keypoint_image) {
                setPreviewKeypointsImage(`data:image/jpeg;base64,${data.keypoint_image}`);
                setKeypointCount(data.count);
            }
        } catch (e) {
            console.error(e);
            setError("Vista previa fallida: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleTrain = async () => {
        if (!image || !label.trim()) return;

        setLoading(true);
        setResult(null);
        setError("");

        const formData = new FormData();
        formData.append("name", label);
        // formData.append("threshold", threshold.toString());
        formData.append("image", image);

        try {
            const response = await fetch(`${URL_Link}/register`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                try {
                    const err = await response.json();
                    throw new Error(err.error || "Registro fallido");
                } catch {
                    throw new Error(`Solicitud fallida con estado ${response.status}`);
                }
            }

            const data = await response.json();
            setMarkdownResult(`
# Registro Exitoso ✅

**Producto**: ${label}

**Estado**: ${data.message}

**Características**: ${keypointCount ? keypointCount + " (de vista previa)" : "Desconocido"}
            `);
            setResult(data.message || 'Modelo actualizado exitosamente');

            // Limpiar formulario después de éxito
            setImage(null);
            setLabel("");

        } catch (error) {
            console.error(error);
            setError(error.message || "Error al entrenar el modelo. Por favor, intenta nuevamente.");
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
        <div className="h-screen md:h-[calc(90vh-8px)] overflow-hidden bg-[#f5f6f8]">
            {/* Línea superior */}
            <div className="border-b-4 md:border-b-8 border-[#ffb703] w-full"></div>

            {/* CONTENEDOR PRINCIPAL */}
            <div className="flex flex-col items-center px-3 md:px-6 pt-3 md:pt-6 text-[#0f2c63] h-[calc(100vh-4px)] md:h-[calc(80vh-8px)]">

                <div className="text-xl md:text-2xl lg:text-3xl font-semibold mb-3 md:mb-4 text-center">
                    Entrenamiento del Modelo
                </div>

                {/* Caja principal de contenido */}
                <div className="w-full md:w-11/12 lg:w-10/12 xl:w-8/12 flex-1 overflow-y-auto px-4 py-4 md:px-8 md:py-8 bg-white rounded-xl md:rounded-2xl shadow-md border border-[#0f2c63]/20 mb-3 md:mb-4">

                    {markdownResult ? (
                        <div className="max-w-2xl mx-auto">
                            <div className="prose prose-sm md:prose-base lg:prose-lg max-w-none">
                                <ReactMarkdown>{markdownResult}</ReactMarkdown>
                            </div>
                            <button
                                onClick={() => {
                                    setMarkdownResult(null);
                                    setImage(null);
                                    setLabel("");
                                }}
                                className="mt-6 w-full py-3 text-sm md:text-base font-medium text-[#0f2c63]/70 hover:text-[#0f2c63] underline"
                            >
                                Registrar otro producto
                            </button>
                        </div>
                    ) : (
                        <>
                            <p className="text-sm md:text-base lg:text-lg text-[#0f2c63]/70 mb-4 md:mb-8 text-center px-2">
                                Sube una imagen y ajusta las características para entrenar el modelo.
                            </p>

                            <div className="flex flex-col gap-4 md:gap-6 max-w-2xl mx-auto">

                                {/* Input de etiqueta */}
                                <div>
                                    <label className="block text-base md:text-lg font-medium mb-2 md:mb-3 text-[#0f2c63]">
                                        Nombre del Producto
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="Ejemplo: laptop_dell, mouse_logitech..."
                                        value={label}
                                        onChange={(e) => setLabel(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        disabled={loading}
                                        className="w-full border-2 border-[#0f2c63] rounded-full px-4 py-2 md:px-6 md:py-3 text-base md:text-lg outline-none focus:border-[#ffb703] transition disabled:opacity-50 disabled:cursor-not-allowed"
                                    />
                                </div>

                                {/* Input de imagen */}
                                {!image && (
                                    <div>
                                        <label className="block text-base md:text-lg font-medium mb-2 md:mb-3 text-[#0f2c63]">
                                            Imagen del Producto
                                        </label>
                                        <ImageInput onChange={(file) => setImage(file ? file : null)} />
                                    </div>
                                )}

                                {/* Editor & Preview Area */}
                                {imagePreview && (
                                    <div className="space-y-4">

                                        {/* Image Display */}
                                        <div className="relative w-full max-w-2xl mx-auto border-2 border-[#0f2c63]/20 rounded-xl overflow-hidden bg-gray-100 flex items-center justify-center">
                                            <button
                                                onClick={() => setImage(null)}
                                                className="absolute top-2 right-2 bg-white/80 p-2 rounded-full text-red-500 hover:text-red-700 hover:bg-white transition-colors z-10"
                                                title="Eliminar imagen"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>

                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img
                                                src={imagePreview}
                                                alt="Preview"
                                                className="w-full h-auto max-h-[400px] object-contain"
                                            />
                                        </div>

                                        {/* Tuning & Actions */}
                                        <div className="p-3 md:p-4 bg-[#f5f6f8] rounded-xl border-2 border-[#0f2c63]/20 space-y-3">
                                            {/* <div>
                                                <div className="text-sm md:text-base font-medium text-[#0f2c63] mb-2">
                                                    Sensibilidad de Características: {threshold.toFixed(3)}
                                                </div>
                                                <input
                                                    type="range"
                                                    min="0.01"
                                                    max="0.1"
                                                    step="0.001"
                                                    value={threshold}
                                                    onChange={(e) => setThreshold(parseFloat(e.target.value))}
                                                    className="w-full"
                                                />
                                            </div> */}

                                            <button
                                                onClick={handlePreview}
                                                disabled={loading}
                                                className="w-full bg-white text-[#0f2c63] border-2 border-[#0f2c63] px-4 py-2 md:py-3 rounded-full text-sm md:text-base font-medium hover:bg-[#0f2c63] hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                            >
                                                {loading ? (
                                                    <>
                                                        <Loader2 className="w-4 h-4 md:w-5 md:h-5 animate-spin" />
                                                        <span>Actualizando...</span>
                                                    </>
                                                ) : (
                                                    <div>

                                                    </div>

                                                    //     <>
                                                    //         <Eye className="w-4 h-4 md:w-5 md:h-5" />
                                                    //         <span>Actualizar Vista Previa</span>
                                                    //     </>
                                                )}
                                            </button>
                                        </div>

                                        {/* Results */}
                                        <div className="p-3 md:p-4 bg-[#f5f6f8] rounded-xl border-2 border-[#0f2c63]/20">
                                            <div className="text-sm md:text-base font-medium text-[#0f2c63] mb-2">
                                                Resultados
                                            </div>
                                            {keypointCount !== null ? (
                                                <div className="p-2 md:p-3 bg-[#ffb703]/20 border-2 border-[#ffb703] rounded-lg text-center">
                                                    <div className="text-lg md:text-xl font-bold text-[#0f2c63]">
                                                        {keypointCount} características encontradas
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="p-2 md:p-3 bg-white border-2 border-[#0f2c63]/20 rounded-lg text-center text-[#0f2c63]/50">
                                                    No hay predicción aún
                                                </div>
                                            )}
                                        </div>

                                        {/* Preview Result */}
                                        {previewKeypointsImage && (
                                            <div>
                                                <div className="text-sm md:text-base font-medium text-[#0f2c63] mb-2">
                                                    Vista Previa de Imagen Procesada
                                                </div>
                                                <div className="border-2 border-[#0f2c63]/20 rounded-xl overflow-hidden">
                                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                                    <img
                                                        src={previewKeypointsImage}
                                                        alt="Processed"
                                                        className="w-full h-auto"
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Botón de entrenar */}
                                <button
                                    onClick={handleTrain}
                                    disabled={!image || !label.trim() || loading}
                                    className="w-full bg-[#0f2c63] text-white px-4 py-3 md:px-6 md:py-4 rounded-full text-base md:text-xl font-medium hover:bg-[#0d2452] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 md:gap-3 mt-2 md:mt-4"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 md:w-6 md:h-6 animate-spin" />
                                            <span className="text-sm md:text-xl">Entrenando modelo...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Upload className="w-5 h-5 md:w-6 md:h-6" />
                                            <span className="text-sm md:text-xl">Registrar Producto</span>
                                        </>
                                    )}
                                </button>

                                {/* Resultado exitoso */}
                                {result && !markdownResult && (
                                    <div className="flex items-center gap-2 md:gap-3 p-3 md:p-4 rounded-xl md:rounded-2xl bg-[#ffb703]/20 border-2 border-[#ffb703] text-[#0f2c63] animate-in fade-in slide-in-from-bottom-4">
                                        <CheckCircle2 className="w-5 h-5 md:w-6 md:h-6 flex-shrink-0" />
                                        <p className="font-medium text-sm md:text-base lg:text-lg">{result}</p>
                                    </div>
                                )}

                                {/* Error */}
                                {error && (
                                    <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-red-50 border-2 border-red-300 text-red-700 text-center">
                                        <p className="font-medium text-sm md:text-base">{error}</p>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>

                {/* MLflow History */}
                <div className="w-full md:w-11/12 lg:w-10/12 xl:w-8/12 mb-4">
                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="flex items-center gap-2 text-[#0f2c63]/70 hover:text-[#0f2c63] font-medium text-sm md:text-base mx-auto"
                    >
                        <History className="w-4 h-4 md:w-5 md:h-5" />
                        {showHistory ? "Ocultar Historial de Versiones" : "Mostrar Historial de Versiones (MLflow)"}
                    </button>

                    {showHistory && (
                        <div className="mt-4 bg-white rounded-xl md:rounded-2xl shadow-md border border-[#0f2c63]/20 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm md:text-base">
                                    <thead className="bg-[#0f2c63] text-white">
                                        <tr>
                                            <th className="px-3 py-2 md:px-4 md:py-3 text-left">Fecha</th>
                                            <th className="px-3 py-2 md:px-4 md:py-3 text-left">Productos</th>
                                            <th className="px-3 py-2 md:px-4 md:py-3 text-left">Run ID</th>
                                            <th className="px-3 py-2 md:px-4 md:py-3 text-left">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#0f2c63]/10">
                                        {versions.map((v) => (
                                            <tr key={v.run_id} className="hover:bg-[#f5f6f8]">
                                                <td className="px-3 py-2 md:px-4 md:py-3 text-[#0f2c63]">{v.date}</td>
                                                <td className="px-3 py-2 md:px-4 md:py-3 text-[#0f2c63]">{v.product_count}</td>
                                                <td className="px-3 py-2 md:px-4 md:py-3 text-[#0f2c63] font-mono text-xs md:text-sm">
                                                    {v.run_id.substring(0, 8)}...
                                                </td>
                                                <td className="px-3 py-2 md:px-4 md:py-3">
                                                    <button
                                                        onClick={() => handleRestore(v.run_id)}
                                                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#ffb703]/20 text-[#0f2c63] rounded-full hover:bg-[#ffb703]/30 text-xs md:text-sm font-medium border border-[#ffb703]"
                                                    >
                                                        <Undo className="w-3 h-3 md:w-4 md:h-4" />
                                                        Restaurar
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                        {versions.length === 0 && (
                                            <tr>
                                                <td colSpan={4} className="px-3 py-6 md:py-8 text-center text-[#0f2c63]/50">
                                                    No se encontraron versiones en MLflow.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}