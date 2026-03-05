"use client"
import { useQuery } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Users } from "@/client"
import AddUser from "@/components/admin/AddUser"
import { columns, type UserTableData } from "@/components/admin/columns"
import { DataTable } from "@/components/data-table"
import PendingUsers from "@/components/pending/PendingUsers"
import useAuth from "@/hooks/useAuth"

export default function AdminPage() {
  const { user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user && !user.is_superuser) {
      router.replace("/")
    }
  }, [user, router])

  const { data: response, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => Users.readUsers({ throwOnError: true }).then((r) => r.data),
    enabled: !!user?.is_superuser,
  })

  const users: UserTableData[] = (response?.data ?? []).map((u) => ({
    ...u,
    isCurrentUser: u.email === user?.email,
  }))

  if (!user?.is_superuser) {
    return null
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Users Management</h1>
      </div>

      {isLoading ? (
        <PendingUsers />
      ) : (
        <>
          <AddUser />
          <DataTable columns={columns} data={users} />
        </>
      )}
    </div>
  )
}
