export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <main className="flex flex-col items-center gap-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          UPSC OS
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          One Solution for UPSC Preparation
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="rounded-lg bg-primary px-6 py-3 text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Get Started
          </a>
        </div>
      </main>
    </div>
  );
}
