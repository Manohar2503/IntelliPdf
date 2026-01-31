import { FileText, Sparkles } from "lucide-react";
import { useDocumentStore } from "@/store/useDocumentStore";

export function Header() {
  const { documentsToday, storageUsed, maxStorage } = useDocumentStore();

  const storagePercent = Math.min(
    100,
    Math.round((storageUsed / maxStorage) * 100)
  );

  return (
    <header className="sticky top-0 z-50 overflow-hidden border-b border-white/10 bg-gradient-to-r from-[#050816] via-[#0b1025] to-[#120b2f]">
      {/* ✨ Stars */}
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute left-6 top-6 h-1 w-1 rounded-full bg-white shadow-[0_0_12px_2px_rgba(255,255,255,0.8)] animate-pulse" />
        <div className="absolute left-28 top-16 h-[2px] w-[2px] rounded-full bg-cyan-300 shadow-[0_0_14px_3px_rgba(34,211,238,0.8)] animate-pulse" />
        <div className="absolute right-16 top-10 h-[2px] w-[2px] rounded-full bg-purple-300 shadow-[0_0_14px_3px_rgba(216,180,254,0.9)] animate-pulse" />
        <div className="absolute right-40 top-20 h-1 w-1 rounded-full bg-white/80 shadow-[0_0_12px_2px_rgba(255,255,255,0.6)] animate-pulse" />
        <div className="absolute left-1/2 top-6 h-[2px] w-[2px] rounded-full bg-fuchsia-300 shadow-[0_0_14px_3px_rgba(232,121,249,0.8)] animate-pulse" />
      </div>

      {/* 🌈 Glow orbs */}
      <div className="pointer-events-none absolute -top-20 -left-20 h-56 w-56 rounded-full bg-cyan-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -right-20 h-56 w-56 rounded-full bg-purple-500/20 blur-3xl" />

      <div className="relative px-6 py-4 backdrop-blur-xl">
        <div className="flex items-center justify-between gap-6">
          {/* LEFT BRAND */}
          <div className="flex items-center gap-4">
            {/* Neon Logo */}
            <div className="relative">
              <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-400/50 via-fuchsia-400/40 to-purple-500/50 blur-xl opacity-80" />
              <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 via-purple-500 to-fuchsia-500 shadow-[0_0_30px_rgba(168,85,247,0.55)]">
                <FileText className="h-6 w-6 text-white drop-shadow" />
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold tracking-tight text-white">
                  IntelliPDF
                </h1>

                <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] font-semibold text-white/80">
                  <Sparkles className="h-3 w-3 text-cyan-300" />
                  Night Mode ✨
                </span>
              </div>

              <p className="text-sm text-white/60">
                Upload • Analyze • Chat with your PDFs in seconds
              </p>
            </div>
          </div>

          {/* RIGHT STATS */}
          <div className="flex items-center gap-4">
            {/* Documents Today */}
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-lg backdrop-blur-xl">
              <div className="text-xs text-white/60">Documents Today</div>
              <div className="text-lg font-extrabold text-white">
                <span
                  className={
                    documentsToday > 0
                      ? "bg-gradient-to-r from-cyan-300 to-fuchsia-300 bg-clip-text text-transparent"
                      : ""
                  }
                >
                  {documentsToday}
                </span>
              </div>
            </div>

            {/* Storage */}
            <div className="w-[240px] rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-lg backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div className="text-xs text-white/60">Storage Used</div>
                <div className="text-xs font-semibold text-white/80">
                  {storagePercent}%
                </div>
              </div>

              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-purple-400 to-fuchsia-400 transition-all"
                  style={{ width: `${storagePercent}%` }}
                />
              </div>

              <div className="mt-2 text-sm font-semibold text-white/90">
                {Math.round(storageUsed)}/{maxStorage} MB
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
