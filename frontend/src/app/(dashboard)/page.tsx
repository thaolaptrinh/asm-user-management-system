"use client"

import useAuth from "@/hooks/useAuth"

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
        Welcome back{user?.email ? `, ${user.email.split("@")[0]}` : ""}
      </h1>
      <p className="text-muted-foreground">
        Overview and quick access to your workspace.
      </p>
    </div>
  )
}
