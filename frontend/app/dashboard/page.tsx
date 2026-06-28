export default function DashboardPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="flex h-16 items-center px-6">
          <h1 className="text-lg font-semibold">UPSC OS</h1>
        </div>
      </header>
      <main className="flex-1 p-6">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-muted-foreground">Welcome to UPSC OS</p>
        </div>
      </main>
    </div>
  );
}
