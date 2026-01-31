import React from 'react';
import { Header } from '@/components/Header';
import { BulkUpload } from '@/components/BulkUpload';
import { DocumentLibrary } from '@/components/DocumentLibrary';
import { SetForAnalysis } from '@/components/SetForAnalysis';

export default function Library() {
  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-[#050816] via-[#0b1025] to-[#120b2f]">
      {/* ✨ Background Glow Orbs */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-fuchsia-500/20 blur-3xl" />
      <div className="pointer-events-none absolute top-1/3 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-purple-500/15 blur-3xl" />

      {/* ✨ Stars */}
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <div className="absolute left-12 top-16 h-1 w-1 rounded-full bg-white shadow-[0_0_12px_2px_rgba(255,255,255,0.7)] animate-pulse" />
        <div className="absolute left-40 top-28 h-[2px] w-[2px] rounded-full bg-cyan-300 shadow-[0_0_14px_3px_rgba(34,211,238,0.8)] animate-pulse" />
        <div className="absolute right-20 top-20 h-[2px] w-[2px] rounded-full bg-purple-300 shadow-[0_0_14px_3px_rgba(216,180,254,0.85)] animate-pulse" />
        <div className="absolute right-44 top-36 h-1 w-1 rounded-full bg-white/80 shadow-[0_0_12px_2px_rgba(255,255,255,0.55)] animate-pulse" />
        <div className="absolute left-1/2 top-10 h-[2px] w-[2px] rounded-full bg-fuchsia-300 shadow-[0_0_14px_3px_rgba(232,121,249,0.85)] animate-pulse" />
      </div>

      <Header />

      <main className="relative mx-auto max-w-7xl px-5 sm:px-6 lg:px-8 py-10">
        {/* ✨ Page Title / Subtitle */}
        <div className="mb-8">
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Your PDF Workspace 🌌
          </h2>
          <p className="mt-2 text-sm sm:text-base text-white/60">
            Upload files, analyze sections, and preview documents with IntelliPDF.
          </p>
        </div>

        {/* Layout */}
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
