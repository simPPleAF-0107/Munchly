import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 p-4">
      <div className="mb-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-3xl font-bold text-primary">Munchly</span>
        </Link>
      </div>
      {children}
    </div>
  );
}
