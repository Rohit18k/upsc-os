export default function SettingsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="flex h-16 items-center px-6">
          <h1 className="text-lg font-semibold">UPSC OS</h1>
        </div>
      </header>
      <main className="flex-1 p-6">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-muted-foreground">Configure your preferences</p>
        </div>
      </main>
    </div>
  );
}
