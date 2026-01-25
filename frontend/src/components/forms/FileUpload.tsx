import * as React from 'react';
import { Upload, X, File, Image, FileText, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface FileUploadProps {
  value?: File[];
  onChange?: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in bytes
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
  onUpload?: (files: File[]) => Promise<void>;
}

interface FileWithProgress {
  file: File;
  progress: number;
  error?: string;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return Image;
  if (type.includes('spreadsheet') || type.includes('csv') || type.includes('excel'))
    return FileSpreadsheet;
  if (type.includes('pdf') || type.includes('document')) return FileText;
  return File;
};

export function FileUpload({
  value = [],
  onChange,
  accept,
  multiple = false,
  maxSize = 10 * 1024 * 1024, // 10MB default
  maxFiles = 10,
  disabled = false,
  className,
  onUpload,
}: FileUploadProps) {
  const [dragActive, setDragActive] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [filesWithProgress, setFilesWithProgress] = React.useState<FileWithProgress[]>([]);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList) return;

    const newFiles: File[] = [];
    const errors: string[] = [];

    Array.from(fileList).forEach((file) => {
      if (maxSize && file.size > maxSize) {
        errors.push(`${file.name} exceeds ${formatFileSize(maxSize)}`);
        return;
      }
      if (maxFiles && value.length + newFiles.length >= maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`);
        return;
      }
      newFiles.push(file);
    });

    if (errors.length > 0) {
      console.warn('File upload errors:', errors);
    }

    if (newFiles.length === 0) return;

    const allFiles = multiple ? [...value, ...newFiles] : newFiles;
    onChange?.(allFiles);

    if (onUpload) {
      setUploading(true);
      setFilesWithProgress(newFiles.map((f) => ({ file: f, progress: 0 })));

      try {
        // Simulate progress
        const interval = setInterval(() => {
          setFilesWithProgress((prev) =>
            prev.map((f) => ({
              ...f,
              progress: Math.min(f.progress + 10, 90),
            }))
          );
        }, 200);

        await onUpload(newFiles);

        clearInterval(interval);
        setFilesWithProgress((prev) =>
          prev.map((f) => ({ ...f, progress: 100 }))
        );

        setTimeout(() => {
          setFilesWithProgress([]);
        }, 1000);
      } catch (error) {
        setFilesWithProgress((prev) =>
          prev.map((f) => ({ ...f, error: 'Upload failed' }))
        );
      } finally {
        setUploading(false);
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (!disabled) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = [...value];
    newFiles.splice(index, 1);
    onChange?.(newFiles);
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
          dragActive && 'border-primary bg-primary/5',
          disabled && 'opacity-50 cursor-not-allowed',
          !disabled && 'cursor-pointer hover:border-primary/50'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
        <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium">
          {dragActive ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          or click to browse
        </p>
        {accept && (
          <p className="text-xs text-muted-foreground mt-2">
            Accepted: {accept}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Max size: {formatFileSize(maxSize)}
        </p>
      </div>

      {/* Upload Progress */}
      {filesWithProgress.length > 0 && (
        <div className="space-y-2">
          {filesWithProgress.map((fp, i) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-muted rounded">
              <File className="h-4 w-4 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{fp.file.name}</p>
                {fp.error ? (
                  <p className="text-xs text-red-500">{fp.error}</p>
                ) : (
                  <Progress value={fp.progress} className="h-1 mt-1" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* File List */}
      {value.length > 0 && !uploading && (
        <div className="space-y-2">
          {value.map((file, index) => {
            const Icon = getFileIcon(file.type);
            return (
              <div
                key={index}
                className="flex items-center gap-3 p-2 bg-muted rounded group"
              >
                <Icon className="h-4 w-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(file.size)}
                  </p>
                </div>
                {!disabled && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
