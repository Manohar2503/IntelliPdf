import { FileText } from 'lucide-react';
import { useDocumentStore } from '@/store/useDocumentStore';

export function Header() {
  const { documentsToday, storageUsed, maxStorage } = useDocumentStore();

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <FileText className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-foreground">PDF Intelligence Hub</h1>
            <p className="text-sm text-muted-foreground">Upload, Manage & Analyze Your PDF Documents</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Documents Today</div>
            <div className={`text-lg font-semibold ${documentsToday > 0 ? 'text-primary' : 'text-foreground'}`}>
              {documentsToday}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Storage Used</div>
            <div className="text-lg font-semibold text-foreground">
              {Math.round(storageUsed)}/{maxStorage}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}