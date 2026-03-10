import { Appearance } from "@/components/common/appearance"
import { Footer } from "@/components/common/footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <div className="bg-muted dark:bg-zinc-900 relative hidden lg:flex lg:items-center lg:justify-center">
        <div className="flex flex-col items-center gap-3 text-center px-8">
          <h1 className="text-4xl font-bold tracking-tight">
            User Management System
          </h1>
          <p className="text-lg text-muted-foreground">
            Secure authentication with TOTP 2FA
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-end">
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-xs">{children}</div>
        </div>
        <Footer />
      </div>
    </div>
  )
}
