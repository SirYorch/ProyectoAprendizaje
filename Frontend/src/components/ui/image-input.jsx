import { useRef } from "react";
import { Upload } from "lucide-react";

export function ImageInput({ label, onChange }) {
    const fileInputRef = useRef(null);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            onChange(file);
        } else {
            onChange(null);
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                {label}
            </label>
            <div
                onClick={handleClick}
                className="w-full h-32 border-2 border-dashed border-zinc-300 dark:border-zinc-600 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors"
            >
                <Upload className="w-8 h-8 text-zinc-400 dark:text-zinc-500 mb-2" />
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    Haz clic para seleccionar una imagen
                </p>
            </div>
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
            />
        </div>
    );
}