import React from 'react';
import { Header } from '@/components/Header';
import { BulkUpload } from '@/components/BulkUpload';
import { DocumentLibrary } from '@/components/DocumentLibrary';
import { SetForAnalysis } from '@/components/SetForAnalysis';

export default function Library() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            {/* <BulkUpload /> */}
            <SetForAnalysis />
          </div>
          <div>
            <DocumentLibrary />
          </div>
        </div>
      </main>
    </div>
  );
}