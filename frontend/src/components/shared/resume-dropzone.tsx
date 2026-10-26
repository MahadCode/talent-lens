"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface ResumeDropzoneProps {
  file: File | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
}

export function ResumeDropzone({ file, onFileSelected, disabled }: ResumeDropzoneProps) {
  const [isDragging, setIsDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type === "application/pdf") {
      onFileSelected(dropped);
    }
  }

  if (file) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center justify-between rounded-2xl border border-primary/30 bg-primary/5 p-4"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-medium text-heading">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
          </div>
        </div>
        <button
          onClick={() => onFileSelected(null)}
          disabled={disabled}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-heading"
          aria-label="Remove file"
        >
          <X className="h-4 w-4" />
        </button>
      </motion.div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/40 hover:bg-muted/40",
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
        <UploadCloud className="h-6 w-6 text-primary" />
      </div>
      <div>
        <p className="text-sm font-medium text-heading">Drop a resume here, or click to browse</p>
        <p className="mt-0.5 text-xs text-muted-foreground">PDF only, up to 10MB</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        disabled={disabled}
        onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
